PLANS/ SECUTITIES/RISKS FOR CORE BACKEND BULK/PRODUCTS/ORDER


But don't allow arbitrary URLs blindly.

Your backend needs protections against things like:

non-image files

enormous files

malicious URLs

internal/private network URLs
timeouts
redirects
unsupported formats

So URL importing should go through a controlled media-import service.


his is exactly the part we need to take seriously if you're building a production-grade TRU Connect.

But one correction: the backend should not spend "a few minutes scanning" every image synchronously before responding. That would destroy the instant experience you're trying to build.

Instead, use a quarantine → scan → approve → publish pipeline.

Cloudinary actually has a malware-detection add-on from Perception Point that is designed for user-generated content such as marketplace product images. It scans uploads asynchronously and can return the result to your application through a callback.

The architecture I'd use
SUPPLIER
   │
   │ Upload image
   ▼
TRU CONNECT API
   │
   │ authenticate user
   │ validate product ownership
   │ validate file size/type
   ▼
CLOUDINARY
   │
   │ Asset = PENDING
   ▼
MALWARE SCAN
   │
   ├───────────────┐
   │               │
 CLEAN           MALICIOUS
   │               │
   ▼               ▼
APPROVED         REJECTED
   │
   ▼
AVAILABLE TO
BUSINESSES

So the business never sees an image until it has passed your security pipeline.

1. Don't trust the phone

This is important.

Your React Native app might say:

filename = coca.jpg
type = image/jpeg
size = 500 KB

You cannot trust that.

A malicious user could rename:

malware.exe

to:

coca.jpg

So your backend/cloud upload pipeline needs its own validation.

Cloudinary's upload configuration lets you restrict allowed formats and file sizes.

For TRU Connect I'd allow something like:

JPEG
PNG
WEBP
HEIC   ← if you decide to support it

and reject everything else.

2. Don't allow arbitrary files into your image pipeline

For your product photos, don't use:

resource_type = auto

blindly.

Your product-photo upload should specifically be an image upload.

For example:

image/*

with server-side restrictions.

Cloudinary itself blocks many executable/malware-prone file formats, including .exe, .apk, .bat, .cmd, .ps1, .sh, etc.

But don't treat Cloudinary's format blocking as your complete security system.

TRU Connect still needs its own validation and authorization.

3. The biggest mistake: publishing immediately

Imagine:

Supplier uploads image
       ↓
Cloudinary
       ↓
product_media created
       ↓
Business sees image

❌ Don't do that.

Instead:

Supplier uploads
       ↓
Cloudinary
       ↓
status = PENDING
       ↓
malware scan
       ↓
APPROVED
       ↓
product becomes visible

Cloudinary's Perception Point integration specifically supports this type of flow: uploaded assets are pending while asynchronously scanned, then approved or rejected.

4. Your database needs media status

This is where your DB becomes important.

I'd add:

product_media
-------------------------
id
product_id
cloudinary_public_id
secure_url
resource_type
format
width
height
sort_order


scan_status
scan_provider
scan_result
scanned_at


created_at
updated_at

For example:

scan_status
-----------
PENDING
APPROVED
REJECTED
ERROR

Then your business catalogue query should effectively behave like:

WHERE product_media.scan_status = 'APPROVED'

So even if an asset exists in Cloudinary, your application won't expose it until approved.

5. And you need PRODUCT status too

For example:

products
----------------
id
supplier_id
name
price
status
created_at
updated_at

You can have:

ACTIVE
ARCHIVED

But media itself has:

PENDING
APPROVED
REJECTED

So imagine:

Coca-Cola 500ml
ACTIVE


Images:


image 1 → APPROVED
image 2 → APPROVED
image 3 → PENDING

The business can see the first two.

The third simply isn't displayed yet.

6. What happens if someone uploads malware?

They get something like:

Upload failed


One of your images could not be processed.


Image:
coke500_3.jpg


Reason:
Security scan failed.


The image has not been published.

And internally:

scan_status = REJECTED
scan_result = MALICIOUS

Never show the malicious asset to another user.

7. Don't make the user wait

This is the important part for your "no lag" goal.

Suppose someone uploads:

10 images

Don't do:

POST /upload


wait 20 seconds
wait 30 seconds
wait...

Instead:

POST /media


202 Accepted
{
    "media_id": "...",
    "status": "PENDING"
}

Then your app says:

Uploading...


✓ Coca-Cola 1
✓ Coca-Cola 2
⏳ Coca-Cola 3

and later:

✓ Coca-Cola 3


All photos ready.

The business never has to wait for the entire security process.

8. Bulk imports become even more interesting

Your bulk system now becomes:

products.xlsx
images.zip
       │
       ▼
TRU CONNECT
       │
       ├── Validate spreadsheet
       │
       ├── Validate ZIP
       │
       ├── Extract safely
       │
       ├── Validate images
       │
       ├── Upload images
       │
       ├── Malware scanning
       │
       ├── Create products
       │
       └── Publish approved media

And importantly:

ZIP files themselves are dangerous.

You shouldn't blindly extract an uploaded ZIP.

You need protections against things like:

../evil.exe

(path traversal)

and:

ZIP containing 500 GB

(zip bomb)

and huge numbers of files.

So the backend should:

ZIP
 ↓
validate archive
 ↓
safe extraction directory
 ↓
limit:
    total size
    compressed size
    extracted size
    file count
    filename/path
 ↓
inspect files
 ↓
accept only supported images

Never execute anything extracted from the ZIP.

In fact, for the first version, you can make the bulk importer accept only images + CSV/XLSX, and reject everything else.

9. Do we need our own antivirus server?

Not necessarily.

You have two reasonable architectures.

Option A — Cloudinary malware detection
TRU Connect
     ↓
Cloudinary
     ↓
Perception Point
     ↓
callback
     ↓
TRU Connect

Cloudinary documents this exact malware-scanning workflow and says the add-on scans user-generated content before it reaches end users.

This is probably the cleanest option for your product-media pipeline.

Option B — Your own scanning layer

You could have:

TRU Connect
      ↓
Quarantine storage
      ↓
Antivirus scanner
      ↓
Cloudinary

For example, an isolated worker could use an antivirus engine.

But I wouldn't build that first if Cloudinary's malware scanning meets your requirements. You're building TRU Connect, not trying to become an antivirus company.

10. There is another security layer: image processing

Even a clean image can be enormous.

Someone could upload:

100 MB

or an image with absurd dimensions.

So validate:

file size
width
height
pixel count
format
MIME/magic bytes

Cloudinary supports upload restrictions such as allowed formats and file-size limits, and its upload presets can enforce these centrally.

You can also normalize images when they enter Cloudinary—for example, resizing them to a maximum resolution and stripping unnecessary metadata.

11. And this fits your 3/5/10 image plans

The security system doesn't change.

FREE
3 images/product
       ↓
validate
       ↓
scan
       ↓
approve
PRO
5 images/product
       ↓
validate
       ↓
scan
       ↓
approve
MAX
10 images/product
       ↓
validate
       ↓
scan
       ↓
approve

The plan limit is checked before upload.

Security scanning happens regardless of the plan.

12. The final TRU Connect media architecture

I'd now define it like this:

                  SUPPLIER APP
                       │
                       │
                 Select image
                       │
                       ▼
              TRU CONNECT API
                       │
             ┌─────────┴─────────┐
             │                   │
        Authentication       Plan limits
             │                   │
             └─────────┬─────────┘
                       │
                  File validation
                       │
                  size / format
                       │
                       ▼
                  CLOUDINARY
                       │
                   PENDING
                       │
                       ▼
              MALWARE SCANNING
                       │
              ┌────────┴────────┐
              │                 │
           APPROVED           REJECTED
              │                 │
              ▼                 ▼
       product_media       Never published
       scan_status=        to businesses
       APPROVED
              │
              ▼
       BUSINESS CATALOGUE
              │
              ▼
       Cloudinary optimized
       delivery URL

And your database only needs to know:

product
   │
   └── product_media
          │
          ├── cloudinary_public_id
          ├── secure_url
          ├── sort_order
          ├── scan_status
          └── scanned_at

This is the production-grade approach I'd use.

And one important thing: the backend should never "execute" an uploaded image. It treats it as untrusted data from the moment it arrives. The goal isn't to spend minutes scanning before doing anything; it's to quarantine it, scan asynchronously, and only make it available after it passes. That gives you both security and the instant UX you're aiming for.

Cloudinary also explicitly recommends malware detection for marketplace/product user-generated content, which is essentially your TRU Connect use case.



Security plan — strong, and here's what I'd add

Your plan is right on every major point: quarantine-then-scan (never synchronous-scan-then-respond), scan_status separate from product status, never trust client-declared filename/MIME, ZIP-specific dangers (path traversal, bombs), Cloudinary's format blocking as one layer not the whole system. A few things I'd add, grounded in what's actually real in this codebase already:

The rate limiter already exists and should gate this too. Same Flask-Limiter + JWT-identity-key pattern I already used (and already fixed a real audit-logging gap in) for connections search — bulk import gets its own policy from day one, with its audit event mapped correctly the first time, not retrofitted like search's was.
XLSX is also a ZIP under the hood (OOXML format) — your ZIP-bomb/path-traversal protections were scoped to images.zip, but the spreadsheet itself needs the same class of defense: size/row-count sanity caps before full parsing, and reading it in a way that can't trigger XML entity expansion.
The malware-scan callback needs its own authentication, separate from the rest of the API. Cloudinary/Perception Point will POST a result back to a TRU Connect endpoint — that's an external service calling in, not a logged-in user, so it can't be JWT-gated like everything else. It needs Cloudinary's webhook signature verified (HMAC against your API secret) before trusting anything in the payload, and it needs to be idempotent — providers retry webhook delivery, so a duplicate callback for the same asset must not double-process or double-log.
Magic-byte validation before the file ever reaches Cloudinary, not just relying on Cloudinary's own format restriction as the first line of defense — reject an obviously-fake image fast, without spending an upload call on it.
Every REJECTED (malicious) upload should be a real audit event, tied to the uploading account — same audit-logging discipline already established elsewhere in this backend, so a pattern of malicious uploads from one account is visible, not just silently discarded per-file.
Original uploaded files (CSV/ZIP) get a short retention window with automatic cleanup, not kept forever and not deleted instantly — useful if a supplier disputes an import result. This reuses the exact scheduler pattern already proven for invitation cleanup (an hourly job registered the same way), not new infrastructure.
Bulk import as a paid-tier gate — captured

Noted clearly, and worth being precise about the mechanism since it's different from the photo-limit pattern: photo limits are "same feature, smaller ceiling." Bulk import for a FREE account isn't a smaller version of the feature — it's not available at all. That means the backend needs a real entitlement check ("does this account's tier include bulk import"), server-verified and never trusting anything the client claims about its own tier, plus hard backend-side limits (max rows, max file size, max images) that apply regardless of tier — the tier check and the safety ceiling are two separate protections, not one.