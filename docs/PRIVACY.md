# Privacy Policy

**Effective Date:** October 20, 2025  
**Application:** HoopsInsight NBA Performance Predictor

---

## Data Collection

### **What We Collect:**

**Locally Stored Data Only:**
- Favorite players (stored in local SQLite database)
- Saved predictions (stored in local SQLite database)
- API response cache (stored in local SQLite database)

**Not Collected:**
- No personal information
- No user accounts or authentication data
- No IP addresses logged
- No cookies or tracking pixels
- No analytics or usage statistics sent to third parties

### **Data Storage:**

All data is stored **locally on your device** in:
- `cache.db` - HTTP cache (automatically expires)
- `nba_cache.db` - User preferences and predictions

**Data Retention:**
- Cache data: Auto-deleted after 6-24 hours (TTL)
- User data: Persists until manually cleared
- No data transmitted to our servers (we don't have servers)

---

## Third-Party Services

### **NBA Data API (balldontlie.io):**

This application makes HTTP requests to:
- **Service:** balldontlie.io
- **Purpose:** Fetch NBA player statistics
- **Data Sent:** Player IDs, season numbers (no personal data)
- **Their Privacy Policy:** https://balldontlie.io/privacy (TODO: verify URL)

**We do not control their data practices.**

---

## Data Security

**Local Security:**
- SQLite databases stored with file system permissions
- No passwords or sensitive data stored
- Cache automatically expires to limit data retention
- WAL mode enabled for database integrity

**Network Security:**
- HTTPS used for all API calls
- SSL verification enabled
- No credentials transmitted except API key (optional)
- API key stored in environment variables or Streamlit secrets

---

## Your Rights

**You Can:**
- Clear all cache data (Clear Cache button)
- Delete favorite players (Remove Favorite button)
- Delete prediction history (manually via database)
- Uninstall the application completely

**Your Data is Yours:**
- All data stored locally on your device
- No cloud storage or remote servers
- You have complete control

---

## Changes to Privacy Policy

We may update this policy. Changes will be reflected in:
- This file's "Effective Date"
- CHANGELOG.md

Continued use after changes constitutes acceptance.

---

## Contact

For questions about this privacy policy:
- Review the code (open source)
- Check documentation: README.md, DEVELOPER_GUIDE.md

---

## Compliance

**GDPR:** Not applicable (no personal data collected, no EU data processing)  
**CCPA:** Not applicable (no personal data sold, no California data processing)  
**Children's Privacy:** Not applicable (no data collection from anyone)

---

**Summary: This is a local-only application. Your data never leaves your device.**

