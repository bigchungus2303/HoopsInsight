# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

### **How to Report:**

1. **Email:** [TODO: Add security contact email]
2. **Include:**
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### **Response Time:**

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Fix Timeline:** Depends on severity

### **Disclosure:**

- Coordinated disclosure after fix is released
- Credit given to reporter (if desired)

---

## Security Measures

### **1. API Key Protection**

- ✅ Never hardcoded
- ✅ Stored in environment variables or st.secrets
- ✅ Not logged or displayed
- ✅ Transmitted over HTTPS only

### **2. Database Security**

- ✅ Local SQLite only (no remote access)
- ✅ WAL mode for concurrency
- ✅ Size limits enforced
- ✅ Proper file permissions
- ✅ No SQL injection (parameterized queries)

### **3. Network Security**

- ✅ HTTPS for all API calls
- ✅ SSL verification enabled
- ✅ Timeouts configured (10s max)
- ✅ Request size limits

### **4. Input Validation**

- ✅ Schema validation on cached data
- ✅ Type checking on user inputs
- ✅ Bounds checking on thresholds
- ✅ Sanitized error messages

### **5. Rate Limiting**

- ✅ Nginx: 30 requests/minute per IP
- ✅ API client: Exponential backoff
- ✅ Cache to minimize API calls

### **6. Access Control**

- ✅ No authentication required (public stats only)
- ✅ No user-generated content
- ✅ No file uploads
- ✅ Read-only except data/logs directories

---

## Known Limitations

### **Not Implemented:**

- ❌ User authentication (not needed - public data only)
- ❌ CAPTCHA (consider if abuse detected)
- ❌ IP banning (rely on Nginx rate limiting)
- ❌ Audit logging (basic logging only)

### **Accepted Risks:**

- **Public API key visible in network requests:**
  - Mitigated by: Free tier API, rate limiting
  - Impact: Limited (API has its own rate limits)

- **Local SQLite (not scalable to millions of users):**
  - Mitigated by: WAL mode, connection pooling
  - Impact: Acceptable for small-medium traffic

---

## Security Checklist for Deployment

- [ ] API keys in secrets.toml or environment (not code)
- [ ] .gitignore includes .env and secrets.toml
- [ ] SSL/HTTPS enabled for production
- [ ] Security headers configured (nginx.conf)
- [ ] CSRF protection enabled (config.toml)
- [ ] Error details hidden from users
- [ ] Database file permissions: 600 or 644
- [ ] Running as non-root user
- [ ] Resource limits configured
- [ ] Rate limiting enabled
- [ ] Dependencies up to date
- [ ] DISCLAIMER.md visible to users
- [ ] PRIVACY.md visible to users

---

## Updates

Check for security updates regularly:

```bash
# Check for outdated packages
pip list --outdated

# Update dependencies
pip install -r requirements.txt --upgrade

# Review changes
git log --oneline

# Run security audit (if tools available)
pip install safety
safety check
```

---

## Contact

For security concerns: [TODO: Add security contact]

For general issues: Open a GitHub issue

---

**Last Updated:** October 20, 2025

