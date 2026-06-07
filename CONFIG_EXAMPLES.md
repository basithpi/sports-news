# Configuration Examples for Daily Uploads

## 📍 Time Zone Conversions

All times are in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS±HH:MM`

### Common Time Zones
| Region | Offset | Example |
|--------|--------|---------|
| IST (India) | +05:30 | 2026-06-08T08:00:00+05:30 |
| UTC | +00:00 | 2026-06-08T02:30:00+00:00 |
| EST (US East) | -04:00 | 2026-06-07T22:30:00-04:00 |
| CST (US Central) | -05:00 | 2026-06-07T21:30:00-05:00 |
| PST (US West) | -07:00 | 2026-06-07T19:30:00-07:00 |
| GMT (UK) | +00:00 | 2026-06-08T02:30:00+00:00 |
| AEST (Australia) | +10:00 | 2026-06-08T12:30:00+10:00 |
| JST (Japan) | +09:00 | 2026-06-08T11:30:00+09:00 |

---

## 🕐 Cron Schedule Examples

Edit the `cron` line in `.github/workflows/daily-shorts-upload.yml`:

### Daily Schedules
```yaml
# Every day at 2:30 UTC (default, 8:00 AM IST)
- cron: '30 2 * * *'

# Every day at 8:00 UTC
- cron: '0 8 * * *'

# Every day at 3:00 UTC
- cron: '0 3 * * *'

# Every day at 12:00 UTC (noon)
- cron: '0 12 * * *'

# Every day at 22:00 UTC (10 PM)
- cron: '0 22 * * *'
```

### Weekly Schedules
```yaml
# Monday, Wednesday, Friday at 2:30 UTC
- cron: '30 2 * * 1,3,5'

# Weekdays only (Mon-Fri) at 2:30 UTC
- cron: '30 2 * * 1-5'

# Weekends only (Sat-Sun) at 2:30 UTC
- cron: '30 2 * * 0,6'

# Mondays only at 2:30 UTC
- cron: '30 2 * * 1'
```

### Every N Hours
```yaml
# Every 6 hours
- cron: '0 */6 * * *'

# Every 12 hours
- cron: '0 */12 * * *'

# Every 4 hours
- cron: '0 */4 * * *'
```

---

## 🎬 Upload Count Scenarios

### Safe Quota (10,000 units/day default)
```yaml
--count 6  # 6 × 1,600 = 9,600 units (safe)
```

### Standard Quota (50,000 units/day after request)
```yaml
--count 15  # 15 × 1,600 = 24,000 units (recommended)
```

### High Volume Quota (100,000+ units/day)
```yaml
--count 30  # 30 × 1,600 = 48,000 units
```

---

## 📅 Publishing Schedules

### Scenario 1: Morning Uploads
**Time**: 8:00 AM IST (2:30 UTC)
**Count**: 15 shorts
**Publish Window**: 8:20 AM - 12:55 PM IST (15-min gaps)

```yaml
--schedule-start "2026-06-08T08:00:00+05:30"
--schedule-interval-minutes 15
--count 15
```

### Scenario 2: Distributed Throughout Day
**Time**: 6:00 AM IST (00:30 UTC)
**Count**: 10 shorts
**Publish Window**: 6:20 AM - 2:50 PM IST (30-min gaps)

```yaml
--schedule-start "2026-06-08T06:00:00+05:30"
--schedule-interval-minutes 30
--count 10
```

### Scenario 3: Prime Time Uploads
**Time**: 6:00 PM IST (12:30 UTC)
**Count**: 15 shorts
**Publish Window**: 6:20 PM - 11:00 PM IST (20-min gaps)

```yaml
--schedule-start "2026-06-08T18:00:00+05:30"
--schedule-interval-minutes 20
--count 15
```

### Scenario 4: Overnight Generate, Morning Publish
**Time**: 2:00 AM IST (20:30 UTC previous day)
**Count**: 15 shorts
**Publish Window**: 8:00 AM - 12:40 PM IST (20-min gaps)

```yaml
--schedule-start "2026-06-08T08:00:00+05:30"
--schedule-interval-minutes 20
--count 15
# Generate at 2 AM, publish starting 8 AM same day
```

---

## 🔄 Workflow Configuration Examples

### Full Workflow Configuration
```yaml
name: Daily YouTube Shorts Upload

on:
  schedule:
    - cron: '30 2 * * *'  # Modify this line
  workflow_dispatch:

jobs:
  upload-shorts:
    runs-on: ubuntu-latest
    steps:
      # ... (other steps remain the same)
      
      - name: Generate and upload shorts
        run: |
          python sports_shorts_pipeline.py \
            --count 15 \
            --schedule-start "2026-06-08T08:00:00+05:30" \
            --schedule-interval-minutes 15
```

### Example 1: 10 Shorts, Weekdays Only
```yaml
on:
  schedule:
    - cron: '30 2 * * 1-5'  # Mon-Fri only

jobs:
  upload-shorts:
    runs-on: ubuntu-latest
    steps:
      # ... other steps ...
      - name: Generate and upload shorts
        run: |
          python sports_shorts_pipeline.py \
            --count 10 \
            --schedule-start "2026-06-08T08:00:00+05:30" \
            --schedule-interval-minutes 20
```

### Example 2: 15 Shorts, Every 6 Hours
```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  upload-shorts:
    runs-on: ubuntu-latest
    steps:
      # ... other steps ...
      - name: Generate and upload shorts
        run: |
          python sports_shorts_pipeline.py \
            --count 15 \
            --schedule-start "2026-06-08T08:00:00+05:30" \
            --schedule-interval-minutes 15
```

### Example 3: Test Mode (No Upload)
```yaml
jobs:
  upload-shorts:
    runs-on: ubuntu-latest
    steps:
      # ... other steps ...
      - name: Generate shorts (test mode)
        run: |
          python sports_shorts_pipeline.py \
            --count 15 \
            --no-upload-youtube
```

---

## 📊 Quota Planning

| Daily Count | Units Needed | Daily Uploads | Recommendation |
|------------|-------------|---------------|-----------------|
| 5 | 8,000 | 5 msgs | ✅ Safe with default quota |
| 10 | 16,000 | 10 msgs | ⚠️ Risky with default, OK with 50k |
| 15 | 24,000 | 15 msgs | ⚠️ Needs 50k quota (RECOMMENDED) |
| 20 | 32,000 | 20 msgs | ❌ Needs 50k quota + monitoring |
| 30 | 48,000 | 30 msgs | ❌ Needs 100k+ quota |

**Recommendation**: Start with 15 shorts/day and request 50,000 quota increase.

---

## 🚨 Important Notes

1. **Minimum interval between publishes**: 15 minutes (YouTube policy)
2. **Default publish time**: If `--schedule-start` not set, first video publishes ~20 min after generation
3. **Timezone format**: Always use ISO 8601 with timezone offset
4. **GitHub Actions UTC only**: Cron times are always in UTC, convert from your timezone
5. **First OAuth run**: Takes longer because of browser authorization (one-time only)

Use [crontab.guru](https://crontab.guru) to verify cron expressions!
