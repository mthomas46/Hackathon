# Secrets Management Guide

## ⚠️ **IMPORTANT: Never Commit Secrets!**

The `.env` file is now excluded from version control to prevent accidental exposure of sensitive credentials.

---

## 🔒 **Setup Instructions**

### **For Development**

1. **Copy the template**:
   ```bash
   cp .env.template .env
   ```

2. **Update with your values**:
   ```bash
   # Edit .env with your actual credentials
   vim .env
   ```

3. **Key values to update**:
   - `DATABASE_URL`: PostgreSQL password
   - `GIT_REPO_PATH`: Absolute path to repository
   - `ENVIRONMENT`: Set to `development`

### **For Staging/Production**

**DO NOT** use `.env` files in production! Use a secrets manager:

#### **Option 1: Environment Variables**
```bash
# Set directly in environment
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://host:6379/0"
```

#### **Option 2: AWS Secrets Manager**
```python
import boto3
import json

def load_secrets():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='ecosystem-mcp/production')
    return json.loads(response['SecretString'])
```

#### **Option 3: HashiCorp Vault**
```bash
# Fetch secrets from Vault
vault kv get -field=database_url secret/ecosystem-mcp/production
```

#### **Option 4: Docker Secrets**
```yaml
# docker-compose.yml
services:
  ecosystem-mcp:
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    external: true
  api_key:
    external: true
```

---

## 🔐 **Security Best Practices**

### **1. Password Strength**
```bash
# Generate strong passwords
openssl rand -base64 32

# For PostgreSQL
# Use at least 16 characters with mix of upper, lower, numbers, symbols
```

### **2. Rotation Schedule**
- **Development**: Every 90 days
- **Staging**: Every 60 days  
- **Production**: Every 30 days

### **3. Access Control**
```bash
# Restrict .env file permissions
chmod 600 .env

# Owner read/write only
-rw------- 1 user user 1234 Oct 11 14:00 .env
```

### **4. Audit Trail**
- Log all secret accesses
- Monitor for unauthorized access
- Alert on secret changes

---

## 🚨 **Emergency: Secrets Exposed**

If secrets are accidentally committed:

### **Immediate Actions**

1. **Rotate ALL exposed secrets immediately**:
   ```sql
   -- PostgreSQL
   ALTER USER ecosystem WITH PASSWORD 'new_secure_password';
   ```

2. **Revoke compromised credentials**:
   ```bash
   # Invalidate API keys
   # Reset database passwords
   # Regenerate service tokens
   ```

3. **Remove from git history**:
   ```bash
   # Use BFG Repo-Cleaner
   bfg --delete-files .env
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # Force push (coordinate with team!)
   git push --force --all
   ```

4. **Notify security team**:
   - Document what was exposed
   - When it was committed
   - Who had access
   - What actions were taken

---

## 📋 **Checklist for New Environments**

- [ ] Copy `.env.template` to `.env`
- [ ] Update all placeholder values
- [ ] Use strong, unique passwords
- [ ] Set correct `ENVIRONMENT` value
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test configuration: `make deploy`
- [ ] Restrict file permissions: `chmod 600 .env`
- [ ] Document secret locations
- [ ] Set up rotation schedule
- [ ] Configure monitoring/alerting

---

## 🔍 **Verification**

### **Check .gitignore**
```bash
git check-ignore .env
# Should output: .env
```

### **Verify not tracked**
```bash
git status --ignored
# .env should be in "Ignored files"
```

### **Test secret loading**
```bash
# Should fail if .env missing
python -c "from src.config import settings; print(settings.database_url)"
```

---

## 📚 **Additional Resources**

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)

---

## 🎯 **Current Status**

✅ `.env` excluded from version control  
✅ `.env.template` created with placeholders  
✅ Documentation provided  
⏳ **TODO**: Implement secrets manager for production  
⏳ **TODO**: Add secret rotation automation  
⏳ **TODO**: Set up secret access auditing

