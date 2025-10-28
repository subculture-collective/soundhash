"""Email template rendering engine."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config.settings import Config
from src.database.connection import db_manager
from src.database.models import EmailTemplate

logger = logging.getLogger(__name__)


@dataclass
class RenderedEmail:
    """Rendered email content."""

    subject: str
    html_body: str
    text_body: Optional[str]
    category: str
    variant: str


class EmailTemplateEngine:
    """Engine for rendering email templates."""

    def __init__(self):
        """Initialize template engine."""
        self.templates_dir = Config.EMAIL_TEMPLATES_DIR
        self.jinja_env = None

        # Initialize Jinja2 if templates directory exists
        if os.path.exists(self.templates_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.templates_dir),
                autoescape=select_autoescape(["html", "xml"]),
            )
            logger.info(f"Initialized Jinja2 templates from {self.templates_dir}")

    async def render_template(
        self, template_name: str, context: Dict[str, Any], language: str = "en"
    ) -> Optional[RenderedEmail]:
        """
        Render an email template.

        Args:
            template_name: Name of the template
            context: Context variables for rendering
            language: Language code

        Returns:
            RenderedEmail object or None if template not found
        """
        # Try to get template from database first
        db_template = await self._get_db_template(template_name, language)

        if db_template:
            return await self._render_db_template(db_template, context)

        # Fall back to file-based templates
        if self.jinja_env:
            return await self._render_file_template(template_name, context, language)

        logger.error(f"Template not found: {template_name} (language: {language})")
        return None

    async def _get_db_template(
        self, template_name: str, language: str = "en"
    ) -> Optional[EmailTemplate]:
        """Get template from database."""
        session = db_manager.get_session()
        try:
            # First try exact match with language
            template = (
                session.query(EmailTemplate)
                .filter_by(name=template_name, language=language, is_active=True)
                .first()
            )

            # Fall back to English if not found
            if not template and language != "en":
                template = (
                    session.query(EmailTemplate)
                    .filter_by(name=template_name, language="en", is_active=True)
                    .first()
                )

            return template
        finally:
            session.close()

    async def _render_db_template(
        self, template: EmailTemplate, context: Dict[str, Any]
    ) -> RenderedEmail:
        """Render a database template."""
        try:
            # Add common context variables
            full_context = self._get_base_context()
            full_context.update(context)

            # Render subject
            subject_template = Environment(autoescape=True).from_string(template.subject)
            subject = subject_template.render(**full_context)

            # Render HTML body
            html_template = Environment(autoescape=select_autoescape(["html"])).from_string(
                template.html_body
            )
            html_body = html_template.render(**full_context)

            # Render text body if exists
            text_body = None
            if template.text_body:
                text_template = Environment(autoescape=False).from_string(
                    template.text_body
                )
                text_body = text_template.render(**full_context)

            return RenderedEmail(
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                category=template.category,
                variant=template.variant,
            )

        except Exception as e:
            logger.error(f"Error rendering template {template.name}: {str(e)}")
            return None

    async def _render_file_template(
        self, template_name: str, context: Dict[str, Any], language: str = "en"
    ) -> Optional[RenderedEmail]:
        """Render a file-based template."""
        try:
            # Add common context
            full_context = self._get_base_context()
            full_context.update(context)

            # Try to load template with language suffix
            html_template_name = f"{template_name}_{language}.html"
            text_template_name = f"{template_name}_{language}.txt"
            subject_template_name = f"{template_name}_{language}_subject.txt"

            # Fall back to English if language-specific not found
            if not self._template_exists(html_template_name):
                html_template_name = f"{template_name}_en.html"
                text_template_name = f"{template_name}_en.txt"
                subject_template_name = f"{template_name}_en_subject.txt"

            # Render HTML
            html_template = self.jinja_env.get_template(html_template_name)
            html_body = html_template.render(**full_context)

            # Render text (optional)
            text_body = None
            if self._template_exists(text_template_name):
                text_template = self.jinja_env.get_template(text_template_name)
                text_body = text_template.render(**full_context)

            # Render subject
            subject = template_name.replace("_", " ").title()
            if self._template_exists(subject_template_name):
                subject_template = self.jinja_env.get_template(subject_template_name)
                subject = subject_template.render(**full_context).strip()

            return RenderedEmail(
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                category="transactional",  # Default for file-based
                variant="A",
            )

        except Exception as e:
            logger.error(f"Error rendering file template {template_name}: {str(e)}")
            return None

    def _template_exists(self, template_name: str) -> bool:
        """Check if a file template exists."""
        if not self.jinja_env:
            return False
        try:
            self.jinja_env.get_template(template_name)
            return True
        except:
            return False

    def _get_base_context(self) -> Dict[str, Any]:
        """Get base context variables for all templates."""
        return {
            "app_name": "SoundHash",
            "app_url": Config.CALLBACK_BASE_URL,
            "support_email": Config.SENDGRID_FROM_EMAIL,
            "unsubscribe_url": Config.EMAIL_UNSUBSCRIBE_URL,
            "current_year": 2025,
        }
