# Injury Exclusion Guide

## 🏥 How to Update Injured Players

### Quick Steps

1. **Open** `pick_configs/picks.yaml`
2. **Find** the `injured_players:` section
3. **Add/Remove** player names
4. **Click** "🔄 Refresh Players" button in Pick of the Day page

---

## 📝 Format

```yaml
injured_players:
  - "FirstName LastName"  # Comment explaining injury
  - "Fred VanVleet"       # Torn ACL - Out for season
  - "LeBron James"        # Sciatica - Out ~1 month
```

**Important**: Use exact name format with quotes!

---

## 🔄 Current Injury List (Oct 21, 2025)

### Out for Season
- **Fred VanVleet** (HOU) - Torn ACL during offseason

### Short-Term (Weeks)
- **LeBron James** (LAL) - Sciatica (~1 month)
- **Jalen Williams** (OKC) - Wrist surgery recovery

### To Update
When players return or new injuries occur:
1. Edit `pick_configs/picks.yaml`
2. Add/remove from `injured_players` list
3. Click "Refresh Players" button in app
4. No restart needed!

---

## 🎯 When to Update

### Add to List
- ✅ Offseason injuries (surgery, etc.)
- ✅ Announced multi-week absences
- ✅ Season-ending injuries
- ✅ Suspensions

### Remove from List  
- ✅ Player returns to lineup
- ✅ Plays 10+ minutes for 3 games
- ✅ Injury report cleared

### Don't Need to Add
- ❌ Day-to-day injuries (auto-detected after DNP)
- ❌ Load management (auto-detected)
- ❌ In-season injuries (auto-detected after 1-3 games)

---

## 📊 Detection Methods

### Automatic (DNP-Based)
- Detects after 1-3 DNPs
- Works for in-season injuries
- No manual update needed

### Manual (Config-Based)
- Required for offseason injuries
- Immediate effect
- Needs periodic updates

### Combined Result
- ✅ Best of both worlds
- ✅ Catches offseason + in-season
- ✅ Easy to maintain

---

## 🔍 Example

### Fred VanVleet Timeline

**Sept 2025**: Torn ACL during offseason workout

**Oct 21, 2025** (Before adding to list):
- ❌ Appears in HOU picks (using 2024 season data)
- Shows as "Active (33.3 min/game)"

**Oct 21, 2025** (After adding to list):
- ✅ Excluded from HOU picks
- Player pool: Alperen Sengun, Jabari Smith Jr. only

**Oct 22-30, 2025** (First week of season):
- 0 minutes in games 1-3
- ✅ Auto-detected via DNP pattern
- Can remove from manual list (auto-detection takes over)

---

## 📋 Maintenance Schedule

### Weekly (Recommended)
- Check injury reports
- Update `injured_players` list
- Click "Refresh Players" button

### Daily (Optional)
- For high-stakes picks
- Verify official injury reports
- Update before generating picks

### As Needed
- Major injury announcements
- Player returns
- Suspension news

---

## 🔗 Injury Report Sources

Suggested sources for updates:
- NBA.com official injury report
- ESPN injury updates
- RotoWire injury news
- Team official announcements

---

**Keep this list updated for accurate picks!** 🏥

Current list at: `pick_configs/picks.yaml` (lines 34-37)

