# Type Checking with mypy

This project uses [mypy](https://mypy.readthedocs.io/) for static type checking to improve code quality and maintainability.

## Configuration

Type checking configuration is in `pyproject.toml` under `[tool.mypy]`.

### Key Settings

- **Python Version**: 3.11
- **Strict Mode**: Disabled globally, but enabled per-module for core functionality
- **SQLAlchemy Plugin**: Enabled for better ORM type support

### Per-Module Configuration

The following modules have strict type checking enabled (`disallow_untyped_defs = true`):

- `src.core.*` - Core audio fingerprinting and video processing
- `src.database.*` - Database models, repositories, and connection
- `src.ingestion.*` - Channel ingestion and video job processing

Other modules (config, api, bots, auth) have type checking but are more lenient.

## Running mypy

To check the entire codebase:

```bash
mypy src scripts
```

To check specific modules:

```bash
mypy src/core/
mypy src/database/
mypy src/ingestion/
```

## Type Hints Guidelines

### Functions

All public functions in strict modules must have type hints:

```python
def process_video(video_id: str, max_retries: int = 3) -> Optional[str]:
    """Process a video and return the file path."""
    ...
```

### Optional Parameters

Use `Optional[T]` for parameters that can be None:

```python
def create_channel(channel_id: str, name: Optional[str] = None) -> Channel:
    ...
```

### SQLAlchemy Models

Use `Mapped` for relationship type hints:

```python
from sqlalchemy.orm import Mapped

class Video(Base):
    fingerprints: Mapped[List["AudioFingerprint"]] = relationship(...)
```

### Third-Party Libraries

Some libraries don't have complete type stubs. These are configured to ignore missing imports:

- librosa, scipy, soundfile
- yt-dlp, ffmpeg
- tweepy, praw
- uvicorn, colorlog, tqdm

## Type Ignore Comments

Use `# type: ignore[code]` sparingly and only when necessary:

```python
value = some_untyped_lib_func()  # type: ignore[no-untyped-call]
```

Always include the specific error code in square brackets.

## CI Integration

Add mypy to your CI pipeline:

```bash
pip install -r requirements-dev.txt
mypy src scripts
```

## Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [SQLAlchemy mypy plugin](https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html)
