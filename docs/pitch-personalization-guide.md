# Pitch Page Personalization Guide

## Overview

The pitch page ([static/pitch.html](../static/pitch.html)) supports URL parameter-based personalization to customize the content for specific companies.

## How It Works

### Basic Usage

Add `?company=COMPANYNAME` to the URL:

```
http://localhost:8000/pitch.html?company=MPAC
http://localhost:8000/pitch.html?company=NESTLE
http://localhost:8000/pitch.html              # Generic version (no personalization)
```

### What Gets Personalized

When a company parameter is provided, the following sections are automatically customized:

1. **Page Title** (browser tab)
   - Generic: "Document Search & Retrieval System..."
   - MPAC: "MPAC Group - Document Search & Retrieval System"

2. **Problem Statement**
   - Generic: "Sales teams waste hours searching..."
   - MPAC: "At MPAC Group, sales and service engineers spend valuable time searching through hundreds of technical PDFs for customer-specific machine configurations..."

3. **Solution Description**
   - Generic: "Our AI-powered system transforms your PDF documentation..."
   - MPAC: "Our AI-powered system transforms MPAC Group's PDF documentation... With instant access to machine specs, maintenance guides, and spare parts information..."

4. **Common Search Scenarios** (NEW section added)
   - Company-specific use cases are inserted after the problem list
   - Example for MPAC:
     - 🔍 Technical specifications for custom packaging lines
     - 🔍 Maintenance procedures for installed equipment
     - 🔍 Spare parts catalogs across product families
     - 🔍 Safety compliance documentation

5. **Call-to-Action (CTA)**
   - Generic: "Ready to Transform Your Document Search?"
   - MPAC: "Ready to Transform MPAC's Technical Documentation Access?"

## Adding New Companies

### Step 1: Edit the pitch.html file

Open [static/pitch.html](../static/pitch.html) and find the `companyConfig` object (around line 588).

### Step 2: Add your company configuration

Insert a new company entry between the existing ones and 'DEFAULT'. Here's the template:

```javascript
'COMPANYNAME': {
    name: 'Full Company Name',
    industry: 'industry description',
    useCases: [
        'First common search scenario',
        'Second common search scenario',
        'Third common search scenario',
        'Fourth common search scenario'
    ],
    challenge: 'description of the specific problem this company faces with document search',
    benefit: 'description of how the solution helps this specific company',
    ctaHeading: 'Ready to Transform [Company]\'s Technical Documentation Access?',
    ctaSubheading: 'Short compelling subheading for this company'
}
```

### Step 3: Example - Adding Nestlé

```javascript
const companyConfig = {
    'MPAC': {
        // ... existing MPAC config ...
    },
    'NESTLE': {
        name: 'Nestlé',
        industry: 'food and beverage manufacturing',
        useCases: [
            'User requirement specifications for packaging equipment',
            'Technical specifications for production line modules',
            'Quality assurance and validation procedures',
            'Equipment acceptance test documentation (FAT, SAT, IQ, OQ, PQ)'
        ],
        challenge: 'production engineers and quality teams search through extensive URS, technical specs, and validation documents for packaging line configurations and compliance requirements',
        benefit: 'instant access to URS documents, technical specifications, and validation procedures streamlines equipment qualification and accelerates production line setup',
        ctaHeading: 'Ready to Transform Nestlé\'s Technical Documentation Access?',
        ctaSubheading: 'Accelerate equipment qualification and compliance workflows'
    },
    'DEFAULT': {
        // ... keep DEFAULT as fallback ...
    }
};
```

### Step 4: Access the personalized page

```
http://localhost:8000/pitch.html?company=NESTLE
```

## Configuration Fields Explained

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Full company name shown throughout the page | "MPAC Group" |
| `industry` | Industry descriptor (currently not displayed, but available for future use) | "packaging machinery" |
| `useCases` | Array of 3-5 common search scenarios specific to this company | See examples above |
| `challenge` | What problem does this company face? (used in Problem section) | "sales engineers spend time searching through..." |
| `benefit` | How does the solution help? (used in Solution section) | "instant access to specs enables..." |
| `ctaHeading` | Main call-to-action heading at page bottom | "Ready to Transform X's Documentation?" |
| `ctaSubheading` | Supporting text under CTA heading | "Empower your teams..." |

## Important Notes

### URL Parameter Format

- **Case-insensitive**: `?company=MPAC` and `?company=mpac` both work
- **Config key must be UPPERCASE**: In the JavaScript, use `'MPAC'` not `'mpac'`
- The code automatically converts the URL parameter to uppercase: `company?.toUpperCase()`

### Special Characters

If your company name has special characters (like apostrophes), **escape them properly**:

```javascript
ctaHeading: 'Ready to Transform McDonald\'s Documentation?',  // ✅ Correct
ctaHeading: 'Ready to Transform McDonald's Documentation?',   // ❌ Wrong - syntax error
```

### Testing

After adding a new company:

1. **Save the file**
2. **Hard refresh** the browser (Ctrl+Shift+R or Cmd+Shift+R)
3. **Open Developer Console** (F12) to see debug messages
4. **Check the console** for:
   ```
   Personalization Script Loaded
   Company parameter: YOURCOMPANY
   Personalizing for: Your Company Name
   ✅ Problem paragraph updated
   ✅ Solution paragraph updated
   ✅ Use cases section added
   ```

### Debugging

If personalization doesn't work:

1. **Check the browser console** for error messages
2. **Verify the company key** matches exactly (case-sensitive in config)
3. **Ensure proper escaping** of quotes in strings
4. **Hard refresh** to clear browser cache
5. **Check network tab** to ensure pitch.html is loading

## Current Companies Configured

| Company | URL Parameter | Industry |
|---------|---------------|----------|
| MPAC Group | `?company=MPAC` | Packaging machinery |
| Nestlé | `?company=NESTLE` | Food and beverage manufacturing |
| Generic (DEFAULT) | (no parameter) | Technical sales |

## Advanced: Dynamic Personalization

The system uses **client-side JavaScript**, so it works with:

- ✅ FastAPI server (`http://localhost:8000/pitch.html?company=X`)
- ✅ Static file servers (VS Code Live Server, nginx, etc.)
- ✅ GitHub Pages or any static hosting
- ✅ No server-side rendering required

This makes it easy to share personalized links without backend changes!

## Future Enhancements

Potential additions to the personalization system:

1. **Industry-specific metrics** (different ROI calculations per industry)
2. **Logo injection** (company logo in header)
3. **Color theming** (company brand colors)
4. **Multiple use case sets** (different scenarios per department)
5. **Localization** (different languages: `?company=MPAC&lang=fr`)

---

**Questions?** Check the source code in [static/pitch.html](../static/pitch.html) starting at line 573 (the `<script>` tag).
