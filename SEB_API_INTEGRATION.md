# SEB Open Banking API Integration Guide

## Overview
SEB provides PSD2 Account Information Services (AIS) API that allows authorized Third Party Providers (TPPs) to access customer account data with consent.

## Requirements

### 1. PSD2 License
- Obtain an AISP (Account Information Service Provider) license from a national competent authority
- In Sweden: Finansinspektionen (Swedish Financial Supervisory Authority)

### 2. Certificates
You need two types of qualified certificates:
- **QWAC (Qualified Website Authentication Certificate)** - For TLS/SSL authentication
- **QSealC (Qualified Seal Certificate)** - For signing API requests

These must be obtained from a Qualified Trust Service Provider (QTSP).

### 3. Developer Portal Registration
1. Register at [https://developer.sebgroup.com](https://developer.sebgroup.com)
2. Create an account (free)
3. Upload your QWAC and QSealC certificates
4. Apply for production access

## API Endpoints

### Base URLs
- **Sandbox**: `https://api-sandbox.sebgroup.com/ais/v8`
- **Production**: `https://api.sebgroup.com/ais/v8`

### Key Endpoints for Bankgiro Transactions

#### 1. Get Accounts
```
GET /accounts
```
Returns list of customer accounts (requires consent)

#### 2. Get Account Transactions
```
GET /accounts/{accountId}/transactions?dateFrom=2026-01-01&dateTo=2026-01-31
```
Returns transactions for a specific account and date range

#### 3. Get Account Details
```
GET /accounts/{accountId}
```
Returns account details including balance

## Authentication Flow

### Step 1: User Consent (OAuth 2.0 + BankID)
1. Redirect user to SEB consent page
2. User authenticates with Mobile BankID
3. User grants consent to access account data
4. SEB redirects back with authorization code

### Step 2: Exchange Code for Access Token
```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code={authorization_code}&
redirect_uri={your_redirect_uri}&
client_id={your_client_id}
```

### Step 3: Use Access Token
```http
GET /accounts/{accountId}/transactions
Authorization: Bearer {access_token}
X-Request-ID: {unique-request-id}
```

## Session Duration
- Long-lived sessions: 180 days
- User consent required for each session

## Implementation Options

### Option A: Full API Integration (Recommended for Production)
**Pros:**
- Fully automated
- Real-time data access
- Secure and compliant

**Cons:**
- Requires PSD2 license (~3-6 months to obtain)
- Requires qualified certificates (~€500-2000/year)
- Complex OAuth + BankID flow
- Requires user consent each time

**Steps:**
1. Apply for AISP license from Finansinspektionen
2. Obtain QWAC and QSealC certificates
3. Register on SEB Developer Portal
4. Implement OAuth 2.0 + BankID consent flow
5. Integrate API calls for account transactions

### Option B: Manual Download + Auto-Process (Current Implementation)
**Pros:**
- No license required
- No certificates needed
- Works immediately
- Simple to use

**Cons:**
- Manual download step required
- Not fully automated

**Steps:**
1. Log into SEB online banking (seb.se)
2. Navigate to account transactions
3. Export transactions as CSV (usually under "Export" or "Ladda ner")
4. Upload CSV file to invoice system
5. System automatically processes and generates Bankgiro report

## Current Implementation

We've implemented **Option B** with the following features:

### Backend Endpoint
```
POST /upload-seb-transactions?year=2026&month=1
Content-Type: multipart/form-data

file: [CSV file from SEB export]
```

### Processing Logic
1. Parses SEB CSV export
2. Filters transactions by date range (year/month)
3. Groups transactions by date
4. Identifies days with >1 Bankgiro payment
5. Generates PDF report with detailed breakdown

### Frontend
- New upload section for SEB transaction files
- Accepts CSV/Excel formats
- Shows processing status
- Displays generated report

## CSV Format Expected

The system expects SEB export with these columns (Swedish names):
- `Bokföringsdatum` or `Transaktionsdatum` - Transaction date
- `Belopp` or `Amount` - Amount
- `Text` or `Beskrivning` - Description

Example:
```csv
Bokföringsdatum,Text,Belopp,Saldo
2026-01-03,FOODORA AB BG:299430175761,18804.31,125000.00
2026-01-03,PAYPAL PTE. LTD Hong Yan AB,6176.90,131176.90
2026-01-04,IZETTLE AB DAILY,3682.46,134859.36
```

## Next Steps

### For Immediate Use (Option B)
1. ✅ Backend endpoint created
2. ✅ CSV parser implemented
3. ✅ PDF report generator updated
4. ✅ Frontend upload UI added
5. 🔄 Deploy and test

### For Future Full Automation (Option A)
1. Apply for AISP license from Finansinspektionen
2. Purchase QWAC and QSealC certificates
3. Register on SEB Developer Portal
4. Implement OAuth 2.0 consent flow
5. Integrate BankID authentication
6. Implement API calls for transactions
7. Store and refresh access tokens

## Cost Estimate for Full API Integration

- **AISP License Application**: Free (but requires legal entity, compliance documentation)
- **QWAC Certificate**: €500-1000/year
- **QSealC Certificate**: €500-1000/year
- **Development Time**: 2-4 weeks
- **Compliance/Legal Review**: Variable

## Resources

- [SEB Developer Portal](https://developer.sebgroup.com)
- [PSD2 Regulation](https://ec.europa.eu/info/law/payment-services-psd-2-directive-eu-2015-2366_en)
- [Finansinspektionen (Swedish FSA)](https://www.fi.se)
- [List of Qualified Trust Service Providers](https://webgate.ec.europa.eu/tl-browser/)

## Support

For API technical support:
- SEB Developer Portal: [https://developer.sebgroup.com/support](https://developer.sebgroup.com/support)
- Create support ticket in Developer Portal

For licensing questions:
- Contact Finansinspektionen: [https://www.fi.se/en/](https://www.fi.se/en/)
