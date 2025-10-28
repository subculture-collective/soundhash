// Custom JavaScript for SoundHash documentation

// Add copy button functionality enhancement
document.addEventListener('DOMContentLoaded', function() {
  // Enhance code blocks with language labels
  document.querySelectorAll('pre code').forEach(function(block) {
    const language = block.className.match(/language-(\w+)/);
    if (language) {
      const label = document.createElement('span');
      label.className = 'code-language-label';
      label.textContent = language[1].toUpperCase();
      block.parentElement.insertBefore(label, block);
    }
  });

  // Add external link icons
  document.querySelectorAll('a[href^="http"]').forEach(function(link) {
    if (!link.hostname.includes('soundhash.io')) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add copy notification
  const copyButtons = document.querySelectorAll('.md-clipboard');
  copyButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      const notification = document.createElement('div');
      notification.className = 'copy-notification';
      notification.textContent = 'Copied!';
      button.appendChild(notification);
      
      setTimeout(function() {
        notification.remove();
      }, 2000);
    });
  });
});

// Analytics tracking (if needed)
// window.dataLayer = window.dataLayer || [];
// function gtag(){dataLayer.push(arguments);}
// gtag('js', new Date());
// gtag('config', 'GA_MEASUREMENT_ID');
