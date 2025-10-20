# Streamlit Configuration

## secrets.toml (DO NOT COMMIT)

Create this file locally and in Streamlit Cloud dashboard:

```toml
[api]
nba_api_key = "your_balldontlie_api_key_here"
```

## config.toml

Application configuration for both local and production.

**Security settings:**
- CSRF protection enabled
- Error details hidden from users
- Usage stats disabled
- Minimal toolbar

**Theme:**
- Base: Light
- Primary: Orange (#FF6B35)
- Clean, professional appearance

