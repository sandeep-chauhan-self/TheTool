# 🌐 Guide 05: Add Custom Domain (Optional)

**Estimated Time:** 10-15 minutes  
**Difficulty:** ⭐⭐ Medium  
**Prerequisites:** Guides 01-04 complete, optional domain registration  
**What You'll Do:** Add a professional domain name to your app  
**What You'll Have After:** App accessible via custom domain (e.g., yourapp.com)  

---

## ⚠️ IMPORTANT: This Guide is OPTIONAL

You can skip this guide if:
- ✓ You're happy with free `vercel.app` subdomain
- ✓ You don't need a custom domain
- ✓ You want to save money (~$8/year)

Your app already works great with:
- Frontend: `yourapp.vercel.app`
- Backend: `yourapp.railway.app`

But a custom domain looks more professional! 👍

---

## When to Use This Guide

Use this guide when you want:
- ✅ Professional looking domain (yourapp.com)
- ✅ Easy to share with others
- ✅ Professional appearance
- ✅ Branded experience

---

## Step 1: Choose a Domain Name

### 1.1 Decide on Your Domain

Pick a domain you like. Examples:
- `stockanalyzer.com`
- `thetool.dev`
- `tradealerts.app`
- Your business name

**Requirements:**
- 3-50 characters
- Letters, numbers, hyphens only
- No special characters

### 1.2 Check Availability

You'll check availability when registering (next step)

---

## Step 2: Register a Domain

### 2.1 Go to Domain Registrar

We recommend **Namecheap** (affordable, reliable):

| Input Method | Action |
|---|---|
| **Mouse** | Open browser, navigate to: `https://namecheap.com` |
| **Keyboard** | Press `Ctrl+L`, type it, press `Enter` |

**ALTERNATIVES:**
- GoDaddy (godaddy.com) - More expensive
- Google Domains (domains.google.com) - Expensive
- DreamHost (dreamhost.com) - Good value

**Using Namecheap for this guide**

### 2.2 Search for Your Domain

| Input Method | Action |
|---|---|
| **Mouse** | Find search box (top of page) |
| | Type your desired domain (e.g., "thetool") |
| | Press Enter or click search |

**WHAT YOU SHOULD SEE:**
```
thetool.com .......................... $8.88/year ✓
thetool.net .......................... $7.48/year ✓
thetool.org .......................... $8.98/year ✓
thetool.app ......................... $12.98/year ✓
(already taken) ..................... UNAVAILABLE ✗
```

Green checkmark = available!

### 2.3 Select Your Domain

| Input Method | Action |
|---|---|
| **Mouse** | Click the domain you want |
| | Usually you want `.com` for best price |

**WHAT YOU SHOULD SEE:**
```
thetool.com selected ✓
Quantity: 1
Price: $8.88 for first year
```

### 2.4 Add to Cart

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add to Cart" button |

**WHAT YOU SHOULD SEE:**
- Item added to cart
- Shows in cart (top-right)
- Option to continue shopping or checkout

### 2.5 Complete Purchase

| Input Method | Action |
|---|---|
| **Mouse** | Click "Cart" or "Checkout" |
| | Enter your information |
| | Complete payment |

**WHAT YOU NEED:**
- Email address
- Name
- Address
- Credit/debit card

**AFTER PAYMENT:**
- Domain is registered to you!
- You own it for 1 year
- Get access to domain management

✅ **You now own the domain!**

---

## Step 3: Get Your Domain's Nameservers

### 3.1 Access Domain Management

After purchase, Namecheap shows domain dashboard:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Log in to Namecheap |
| | 2. Go to "Dashboard" |
| | 3. Find your domain in list |
| | 4. Click "Manage" button |

**WHAT YOU SHOULD SEE:**
- Domain management panel
- Many settings/tabs
- "Nameservers" section

### 3.2 Note the Current Nameservers

You might see something like:
```
ns1.namecheap.com
ns2.namecheap.com
ns3.namecheap.com
ns4.namecheap.com
```

**For Vercel + Railway, you have two options:**
1. **Keep Namecheap nameservers** (easier) → add DNS records
2. **Point to Vercel nameservers** (advanced) → Vercel manages DNS

**We'll use Option 1** (easier for beginners)

---

## Step 4: Configure DNS in Vercel

### 4.1 Add Domain to Vercel

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Vercel dashboard |
| | 2. Select your project |
| | 3. Click "Settings" tab (top) |
| | 4. Click "Domains" (left sidebar) |

**WHAT YOU SHOULD SEE:**
- "Add Domain" button
- Empty domains list (first time)

### 4.2 Add Your Custom Domain

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add Domain" button |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Domain | Your domain (e.g., `thetool.com`) |

| Input Method | Action |
|---|---|
| **Mouse** | Type your domain, click "Add" |

**WHAT VERCEL SHOWS:**

You'll see a prompt showing DNS records:

```
To point your domain to Vercel, add these DNS records:

For root domain (thetool.com):
  Type: A
  Name: @
  Value: 76.76.19.5

For www subdomain (www.thetool.com):
  Type: CNAME
  Name: www
  Value: cname.vercel-dns.com
```

**COPY THESE DNS RECORDS** - you need them for Namecheap!

### 4.3 Keep Vercel Tab Open

Don't close Vercel yet - you'll need these values!

---

## Step 5: Add DNS Records to Namecheap

### 5.1 Open Namecheap in Another Tab

Keep Vercel open, open new browser tab:

| Input Method | Action |
|---|---|
| **Keyboard** | Press `Ctrl+T` (new tab) |
| **Mouse** | Log in to Namecheap again |

### 5.2 Find DNS Management

| Input Method | Action |
|---|---|
| **Mouse** | 1. Namecheap Dashboard |
| | 2. Find your domain |
| | 3. Click "Manage" button |
| | 4. Click "Advanced DNS" tab |

**WHAT YOU SHOULD SEE:**
- List of DNS records
- May have default records already
- Button "Add New Record"

### 5.3 Add First DNS Record (A Record)

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add New Record" button |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Type | A |
| Host | @ |
| Value | 76.76.19.5 (from Vercel) |
| TTL | 3600 |

| Input Method | Action |
|---|---|
| **Mouse** | Click green checkmark to save |

**WHAT YOU SHOULD SEE:**
- Record appears in list with green checkmark
- Status: "Setting up..."

### 5.4 Add Second DNS Record (CNAME for www)

| Input Method | Action |
|---|---|
| **Mouse** | Click "Add New Record" button again |

**FORM TO FILL:**

| Field | Value |
|---|---|
| Type | CNAME |
| Host | www |
| Value | `cname.vercel-dns.com` |
| TTL | 3600 |

| Input Method | Action |
|---|---|
| **Mouse** | Click green checkmark to save |

**WHAT YOU SHOULD SEE:**
```
✓ @ A 76.76.19.5
✓ www CNAME cname.vercel-dns.com
```

---

## Step 6: Wait for DNS Propagation

### 6.1 DNS Takes Time

After adding DNS records:

**IMPORTANT: DNS can take 24-48 hours to fully propagate!**

But usually:
- 5-15 minutes: Most regions work
- 24 hours: Definitely works everywhere

### 6.2 Test Your Domain

After waiting (at least 5 minutes):

| Input Method | Action |
|---|---|
| **Mouse** | Open new browser tab |
| | Type your domain (e.g., `thetool.com`) |
| | Press Enter |

**POSSIBLE RESULTS:**

| Result | Meaning | Action |
|---|---|---|
| App loads! | ✅ DNS working | Continue! |
| "Cannot find page" | DNS not ready yet | Wait 30 min, retry |
| "Vercel error" | Server needs config | See troubleshooting |

### 6.3 Test www Subdomain

| Input Method | Action |
|---|---|
| **Mouse** | Try: `www.thetool.com` |

**WHAT YOU SHOULD SEE:**
- Same app loads
- Both work (with and without www)

✅ **Custom domain is working!**

---

## Step 7: Configure Backend Domain (Optional)

If you want your backend on a custom domain too:

### 7.1 Create Subdomain for Backend

**OPTION A: Use API subdomain**

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go back to Namecheap Advanced DNS |
| | 2. Add new record |

**ADD DNS RECORD:**

| Field | Value |
|---|---|
| Type | CNAME |
| Host | api |
| Value | (Railway CNAME - see next) |
| TTL | 3600 |

### 7.2 Get Railway CNAME Value

To find Railway's CNAME:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Railway dashboard |
| | 2. Find your backend service |
| | 3. Settings → Networking |
| | 4. Look for custom domain option |

Railway should provide a CNAME value like:
```
cname.railway.app
```

Use that value in the DNS record above.

### 7.3 Verify Backend Domain

After DNS propagates (5-30 min):

| Input Method | Action |
|---|---|
| **Mouse** | Try: `https://api.thetool.com/health` |

**WHAT YOU SHOULD SEE:**
```json
{"status": "healthy"}
```

✅ Backend domain working!

### 7.4 Update Frontend Configuration

Now update frontend to use new domain:

| Input Method | Action |
|---|---|
| **Mouse** | 1. Vercel dashboard |
| | 2. Your project → Settings |
| | 3. Environment Variables |
| | 4. Find `REACT_APP_API_URL` |
| | 5. Change value to: `https://api.thetool.com` |
| | 6. Save |

| Input Method | Action |
|---|---|
| **Mouse** | 1. Go to Deployments tab |
| | 2. Click "Redeploy" on latest |
| | 3. Wait for build complete |

Your frontend now uses your custom backend domain! ✅

---

## Step 8: Update GitHub URLs (Optional)

Update your GitHub repo to reflect new URLs:

### 8.1 Update README.md

| Input Method | Action |
|---|---|
| **Mouse** | 1. GitHub repo page |
| | 2. Edit README.md |
| | 3. Replace old URLs with new ones |

**Example:**
```markdown
**Live App:** https://thetool.com
**API:** https://api.thetool.com
**Frontend Repo:** [GitHub](https://github.com/you/TheTool)
```

### 8.2 Commit Changes

```powershell
git add README.md
git commit -m "Update README with custom domain URLs"
git push origin main
```

---

## 🎉 Guide 05 Complete!

### What You've Accomplished:
✅ Registered custom domain (e.g., thetool.com)  
✅ Configured DNS records  
✅ Connected domain to Vercel frontend  
✅ Verified custom domain works  
✅ Optionally connected backend domain  
✅ Updated frontend configuration  

### Your App Now Available At:
- **Professional Frontend:** `https://yourapp.com`
- **Professional Backend (Optional):** `https://api.yourapp.com`
- **Still Works:** `yourapp.vercel.app` and `yourapp.railway.app`

### DNS Summary:

```
yourapp.com
├─ @ (A record) → Points to Vercel
└─ www (CNAME) → cname.vercel-dns.com

api.yourapp.com (optional)
└─ (CNAME) → cname.railway.app
```

---

## Troubleshooting Guide 05

### Problem: "Cannot find page" / "ERR_NAME_NOT_FOUND"
**Solution:**
1. DNS not propagated yet - wait 5-30 minutes
2. Check Namecheap DNS records are added correctly
3. Try `nslookup yourapp.com` in PowerShell to check
4. Try clearing browser cache: Ctrl+Shift+Delete

### Problem: "404 Not Found" from Vercel
**Solution:**
1. Domain added to Vercel but Vercel can't reach it
2. Go to Vercel → Settings → Domains
3. Check domain status (should say "Valid Configuration")
4. May need to wait 10-15 minutes more

### Problem: "Vercel / Railway nameserver prompt"
**Solution:**
1. You can ignore if using Namecheap nameservers
2. Alternative: Follow Vercel's prompt to use their nameservers
3. Both methods work - choose one approach, don't mix

### Problem: "Domain works but API still calls old URL"
**Solution:**
1. Update `REACT_APP_API_URL` in Vercel environment variables
2. Redeploy frontend: Click "Redeploy" button
3. Wait for build complete (2-3 min)
4. Hard refresh frontend: Ctrl+Shift+R

### Problem: "SSL certificate error"
**Solution:**
1. Vercel auto-generates SSL certificates (usually instant)
2. If error persists:
   - Wait 5-10 minutes (certificate generation in progress)
   - Check Vercel dashboard for certificate status
   - Manually refresh after 10 minutes

### Problem: "www version doesn't work"
**Solution:**
1. Verify www CNAME record in Namecheap
2. Check it points to: `cname.vercel-dns.com`
3. Wait 10-15 minutes for DNS propagation
4. Try direct domain without www: `yourapp.com`

---

## Cost Summary

| Item | Cost | Duration |
|---|---|---|
| Domain Registration | $8-12 | 1 year |
| Renewal (each year after) | $8-12 | 1 year |
| Vercel Frontend | $0 | Forever |
| Railway Backend | $1-10/mo | Monthly |
| **Total First Year** | ~$20-30 | All included |
| **Total Per Year After** | ~$20-30 | All included |

**Very affordable for professional app!**

---

## What's Next

Custom domain is optional and now complete!

**Next Guide (Recommended):**
→ `06_MONITORING_MAINTENANCE.md`

In that guide:
- ✅ Set up error alerts
- ✅ Monitor app performance
- ✅ Track costs
- ✅ Maintenance checklist

---

## Summary

Your app now has:
- ✅ Professional custom domain
- ✅ All services working together
- ✅ Automatic deployments
- ✅ 24/7 availability
- ✅ Global CDN (fast worldwide)
- ✅ SSL/HTTPS (encrypted)

**You have a fully deployed, professional app!** 🚀

---

**Guide 05 Status:** ✅ Complete (Optional)  
**Domain Status:** ✅ Configured  
**Time Spent:** ~10-15 minutes  
**Next Guide:** 06_MONITORING_MAINTENANCE.md (Recommended)  
**Estimated Remaining Time:** ~10 minutes
