"""
SupplierProfile -- a supplier's own core identity record: the business
name, category, general location, and verification-adjacent fields a
Business needs to recognise a real-world supplier during search
(file.txt/FILE2.txt Phase 1). Lives HERE, in domains/supplier/
supplier_profile/, not inside network/connections -- this
domain was already reserved (empty scaffolding) for exactly this
purpose, and FILE2.txt explicitly warns against "duplicate Supplier
models". network/connections's service queries this model via
SupplierProfileRepository; it does not own a copy of this data.

ONE-TO-ONE WITH User: supplier_id is unique, not just indexed -- a
supplier's identity lives on auth.users (the root identity, per
user.py's own docstring: "Business/Supplier profile data... belongs on
future BusinessProfile / SupplierProfile models, connected to this
User by a relationship"); this table is exactly that promised
relationship being fulfilled for the Supplier side, mirroring how
BusinessProfile already does it for Business -- verified directly
against business_profile.py: its own FK column is named `business_id`
(not `user_id`), so this column is named `supplier_id` to match that
exact domain-role-prefixed convention, not a generic name.

SEARCH FIELDS ARE NORMALIZED, NEVER DISPLAY FIELDS: normalized_phone /
normalized_email exist purely for indexed exact-match search (see
repositories/supplier_profile_repository.py) -- display always reads
from the User row's own phone_number/email (or, for masking, goes
through shared.helpers.mask_email / a phone equivalent), never from
these columns directly, so this table never becomes a second source of
truth for a supplier's actual contact details.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class SupplierVerificationStatus(str, enum.Enum):
    """Deliberately separate from auth.users.verification_status
    (account-level, real, generic across Business/Supplier) -- this is
    the SUPPLIER-specific commercial trust indicator file.txt's own
    verification-wall phase describes ("stronger commercial
    verification" for suppliers specifically). Two different concepts
    that happen to share similar-looking states; keeping them as
    separate columns/enums avoids one overloading the other's meaning
    later when the verification wall (file.txt Phase 21+) is built."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class PhotoVisibility(str, enum.Enum):
    """WHO can see the resolved photo (see visible_image_source below
    for WHICH photo). Default is CONNECTIONS, not EVERYONE -- agreed
    during architecture review: showing a photo in bare search
    results (before any relationship exists) is a different, more
    exposed choice than showing it to someone you're already
    connected with, and the cautious default should require an
    explicit opt-in to go wider, not a silent one."""

    EVERYONE = "everyone"
    CONNECTIONS = "connections"
    NOBODY = "nobody"


class VisibleImageSource(str, enum.Enum):
    """WHICH photo gets shown, once photo_visibility already allows
    showing one at all. PERSONAL reads live from auth.users.
    profile_image_url (see that column's own docstring on why it's
    never copied here); BUSINESS reads business_image_url on this
    same row. NONE is the default -- nothing shows until the person
    actively picks one, even if photo_visibility would otherwise
    allow it."""

    PERSONAL = "personal"
    BUSINESS = "business"
    NONE = "none"


class SupplierIngestionMode(str, enum.Enum):
    """How a supplier's offers get into TruConnect.

    MANUAL  -- typed in, one at a time, on the phone or the web.
    CSV     -- a spreadsheet or price file, uploaded and mapped.
    API     -- pushed from the supplier's own system.

    NOT A TIER AND NOT A PERMISSION -- see the ingestion_mode column's
    own comment below. It selects which surface to offer, nothing more;
    every path writes the identical SupplierOffer.

    NAME == VALUE, deliberately, unlike PhotoVisibility and
    VisibleImageSource above. SQLAlchemy's Enum(PyEnumClass) persists a
    member's NAME to Postgres, not its .value, so an enum whose values
    differ in case from its names stores something other than what it
    reads like. This codebase has already had to correct a Postgres enum
    for exactly that mismatch (ConnectionRequestStatus). Matching them
    sidesteps the whole class of bug by construction, the same way
    ProductCategory and ProductUnit do.
    """

    MANUAL = "MANUAL"
    CSV = "CSV"
    API = "API"


class SupplierKind(str, enum.Enum):
    """What sort of business this supplier IS.

    STATED, NEVER INFERRED, and that is the entire reason the column
    exists. "Explore wholesalers" has to filter on something, and the
    obvious something -- the business NAME -- is wrong in both
    directions at once. The dev database makes it concrete:

        "Qwen Wholesale"         a name filter would match
        "Lepelle Wholesalers"    would match
        "Seshego Cash & Carry"   is a wholesaler, would NOT match
        "MacMan Businesses"      would not match

    and a retailer trading as "Wholesale Beauty Supplies" would be
    listed having done nothing wrong. A screen that can be entered by
    renaming a business is not a filter, it is a keyword.

    WHY NOT INFER IT FROM BEHAVIOUR EITHER. There are real signals --
    selling by CASE, a minimum order, a wide catalogue -- and they are
    tempting because they need no migration. They are also wrong often
    enough to matter: a spaza selling single units through TruConnect is
    not a retailer for that reason, and a brand-new wholesaler with
    three products is still a wholesaler. Behaviour may CORROBORATE a
    declaration; it cannot replace one.

    UNSPECIFIED IS A REAL ANSWER, not a gap to be filled in later by a
    heuristic. It is what every supplier already in the database is,
    honestly, and nothing should quietly rewrite it.

    NAME == VALUE, for the reason SupplierIngestionMode explains above.
    """

    WHOLESALER = "WHOLESALER"
    DISTRIBUTOR = "DISTRIBUTOR"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"
    UNSPECIFIED = "UNSPECIFIED"


class SupplierPlanTier(str, enum.Enum):
    """What this supplier pays for, and therefore what reach they get.

    NOT A PERMISSION AND NOT A CURTAIN (V2_16). A FREE supplier who is
    verified is findable, orderable, and appears in every EARNED rail
    their stock belongs in. Tiers buy REACH BEYOND WHAT YOU HAVE
    EARNED -- they do not buy the right to exist, and they cannot buy
    another supplier's absence.

    WHAT EACH TIER MAY MOVE is decided in ONE place, outside this
    model and outside demand/: network/community/placement. Nothing in
    the demand engine may read this column -- it is supplier-blind by
    architecture test, and that is what stops the feed becoming an
    auction.

    PARTNER IS SALES-NEGOTIATED and time-boxed via plan_expires_at. A
    permanent unlabelled advantage is how a marketplace quietly becomes
    one supplier's storefront.

    NAME == VALUE, same reason as above.
    """

    FREE = "FREE"
    PRO = "PRO"
    MAX = "MAX"
    PARTNER = "PARTNER"


class SupplierProfile(BaseModel):
    __tablename__ = "supplier_profiles"
    __table_args__ = (
        db.UniqueConstraint("supplier_id", name="uq_supplier_profiles_supplier_id"),
        # Both search paths need their own index -- phone and email
        # are looked up independently, never together, so a single
        # composite index wouldn't serve either query well.
        db.Index("ix_supplier_profiles_normalized_phone", "normalized_phone"),
        db.Index("ix_supplier_profiles_normalized_email", "normalized_email"),
        db.Index("ix_supplier_profiles_business_name", "business_name"),
        {"schema": "supplier"},
    )

    supplier_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)

    # 4-character random code (see algorithms/supplier_code_generator.py
    # for the full generation reasoning) -- a real, permanent identity
    # assigned once, on creation. Never guessable, never sequential --
    # scopes an order reference lookup to this one supplier's own
    # namespace, and carries no information about how many orders this
    # supplier has ever received (that stays hidden, on purpose).
    # Nullable at the schema level only because existing rows need a
    # migration-time backfill before this can be made NOT NULL; every
    # NEW supplier gets one immediately, see the creation repository.
    supplier_code = db.Column(db.String(4), nullable=True, unique=True)

    business_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(120), nullable=True)
    # General only (suburb/city) -- file.txt §4's privacy framing
    # applies to what's STORED for search purposes here too, not just
    # what's returned: this column was never designed to hold a full
    # street address.
    location = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(500), nullable=True)

    # The supplier's own fixed premises -- set ONCE by the supplier
    # via the same MapPickerModal the business's DELIVER flow uses
    # (dashboard/shared/location-picker/), not per order. Deliberately
    # SEPARATE columns from `location` above, never merged into it:
    # `location` is the general suburb/city shown in wide, un-connected
    # search results (see its own comment on the privacy framing that
    # applies), while these are a real, precise street address --
    # exposed ONLY to businesses with an ACTIVE connection, same
    # connected-only gate as whatsapp_number/contact_email below (see
    # connections' catalog_service `contact` block for the identical
    # pattern this mirrors). Building is the one field never populated
    # by reverse-geocoding -- Mapbox has no such concept -- always
    # supplier-typed.
    collection_building = db.Column(db.Text, nullable=True)
    collection_street = db.Column(db.Text, nullable=True)
    collection_suburb = db.Column(db.Text, nullable=True)
    collection_city = db.Column(db.Text, nullable=True)
    collection_province = db.Column(db.Text, nullable=True)
    collection_postal_code = db.Column(db.Text, nullable=True)
    collection_latitude = db.Column(db.Numeric(9, 6), nullable=True)
    collection_longitude = db.Column(db.Numeric(9, 6), nullable=True)

    # FULFILMENT TERMS -- the two facts an informal business needs
    # before it can decide whether it can buy here at all: "will you
    # bring it to me, or must I fetch it", and "how much must I spend
    # to order". Neither existed before: delivery was only ever chosen
    # per-order by the BUSINESS (StockOrderDeliveryType), with the
    # supplier able to decline afterwards
    # (CANNOT_FULFIL_DELIVERY_AREA) -- which meant a business could
    # build a whole cart before discovering the supplier doesn't
    # deliver to them. These state it up front, on the profile.
    #
    # DELIBERATELY UNGATED (shown before any connection exists, like
    # business_image_url/cover_image_url above): these are shopfront
    # terms a business needs while DECIDING whether to connect, not
    # private contact details. Contrast the collection_* columns
    # above, which are a real street address and stay connection-only.
    #
    # THREE STATES, NOT TWO -- NULL means "hasn't said yet", which is
    # genuinely different from False ("says they don't deliver").
    #
    # This started as NOT NULL DEFAULT FALSE and that was WRONG, caught
    # by 31 checkout tests failing at once: a boolean conflates "said
    # no" with "hasn't said", and both halves of that conflation cause
    # a real bug. On DISPLAY, it made the profile assert "Collection
    # only" for a supplier who had never touched the setting -- stating
    # something on their behalf that they never said, exactly what this
    # codebase's own "never show what isn't real" rule exists to
    # prevent. On CHECKOUT, it blocked delivery orders to every
    # existing supplier, removing functionality that worked the day
    # before, on the strength of an answer none of them had given.
    #
    # So: only an EXPLICIT False blocks a DELIVER order
    # (checkout_service._validate_supplier_fulfilment_terms), and only
    # a non-NULL value renders a delivery row at all.
    offers_delivery = db.Column(db.Boolean, nullable=True)
    # NULL means "no minimum", which is genuinely different from 0 --
    # cents, matching every other money column in this codebase (never
    # a float; see shared/finance for the rule).
    minimum_order_cents = db.Column(db.Integer, nullable=True)

    # WHICH PAYMENT RAILS THIS SUPPLIER ACCEPTS.
    #
    # There are exactly two, and the difference between them is not the
    # instrument -- it is whether TruConnect can see the money at all:
    #
    #   DIRECT  -- settled between the two parties, by whatever means
    #              suits them: notes on delivery, an EFT, a bank
    #              deposit, a transfer with a screenshot. TruConnect
    #              observes NONE of it. Capped, because invisible
    #              money is exactly what the caps exist to bound.
    #   DIGITAL -- settled through TruConnect's own gateway. Observed,
    #              so it needs no cap at all.
    #
    # "Cash" and "proof of payment" used to be modelled as two separate
    # methods with two different per-transaction caps, on the reasoning
    # that a traceable transfer is safer than notes. That was a
    # distinction TruConnect could never actually enforce: nothing
    # stops a buyer selecting proof-of-payment for the higher cap and
    # then handing over cash. One rail, one cap, honestly named.
    #
    # PLAIN BOOLEANS, not tri-state. Unlike offers_delivery above,
    # false here is a real and safe answer -- "I don't take that" -- and
    # the defaults assert nothing awkward on anyone's behalf: every
    # supplier already takes direct payment today, and nobody can take
    # digital yet because the gateway is not wired.
    #
    # AT LEAST ONE MUST BE TRUE. A supplier accepting neither cannot be
    # paid at all, which is not a configuration, it is a broken
    # shopfront -- supplier_profile_service refuses it.
    accepts_direct_payment = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    accepts_digital_payment = db.Column(db.Boolean, nullable=False, default=False, server_default="false")

    # ------------------------------------------------------------------
    # SUPPLIER CAPABILITIES
    #
    # CAPABILITIES, NOT A TIER ENUM, and that is the whole point
    # (docs/v2/V2_00_ARCHITECTURE_EVOLUTION section 2.2). It is tempting
    # to write SupplierTier = SMALL | MEDIUM | LARGE and branch on it,
    # and it is wrong: "tier" is really five independent axes that merely
    # correlate. A hustler who wants digital-only is reasonable. A large
    # wholesaler who wants approval for NEW customers only is reasonable.
    # One enum makes both unrepresentable, and the first supplier who
    # does not fit the box arrives in week two.
    #
    # This codebase already made that mistake once at smaller scale:
    # cash and proof-of-payment carried two separate per-transaction
    # caps until it turned out the differentiation was not real, and
    # they collapsed into the single direct_transaction_cap_cents the
    # comment above describes. A tier enum is that bug at five times the
    # size.
    #
    # The two accepts_* booleans above are already capabilities; these
    # simply join them. Nothing in the codebase asks "what tier is this
    # supplier" -- it asks "can this supplier do X".
    # ------------------------------------------------------------------

    # "Businesses must be connected to me before they can order."
    #
    # DEFAULT FALSE, which reverses V1. Connection used to be a hard gate
    # on ordering; in v2 it becomes a choice, and most suppliers should
    # not want it. It exists for the small supplier who genuinely wants
    # to know who is buying before stock moves.
    #
    # A supplier whose orders arrive from their own system CANNOT use
    # this -- there is nobody sitting there to click accept -- which is
    # exactly why it is a capability and not a platform rule.
    requires_connection = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )

    # How this supplier's offers reach TruConnect.
    #
    # NOT A PERMISSION AND NOT A SIZE. It records how the catalogue is
    # maintained so the right surface can be offered -- a MANUAL supplier
    # is not shown a column-mapping screen, an API supplier is not asked
    # to retype 3,000 rows. Every ingestion path writes the SAME
    # SupplierOffer; this only says which door it came through
    # (V2_00 section 2.5).
    ingestion_mode = db.Column(
        db.Enum(SupplierIngestionMode, name="supplier_ingestion_mode", schema="supplier"),
        nullable=False,
        default=SupplierIngestionMode.MANUAL,
        server_default=SupplierIngestionMode.MANUAL.value,
    )

    #: What sort of business this is. STATED by the supplier or by
    #: staff, never derived from the business name -- see SupplierKind.
    supplier_kind = db.Column(
        db.Enum(SupplierKind, name="supplier_kind", schema="supplier"),
        nullable=False,
        default=SupplierKind.UNSPECIFIED,
        server_default=SupplierKind.UNSPECIFIED.value,
    )

    #: What they pay for. DEFAULT FREE, and free is a full member of the
    #: platform rather than a trial (V2_16 Part 5): starve the free tier
    #: and the catalogue thins, and paying suppliers are buying
    #: attention that a healthy catalogue creates.
    plan_tier = db.Column(
        db.Enum(SupplierPlanTier, name="supplier_plan_tier", schema="supplier"),
        nullable=False,
        default=SupplierPlanTier.FREE,
        server_default=SupplierPlanTier.FREE.value,
    )

    #: When a paid plan lapses back to FREE. NULL means "does not
    #: expire", which is right for FREE and for an open-ended
    #: subscription; a PARTNER agreement and a promotional trial both
    #: set it, because a time-boxed advantage is the only honest kind.
    #:
    #: NOTHING ENFORCES IT YET. Whatever reads plan_tier must treat an
    #: expiry in the past as FREE rather than trusting the column -- a
    #: lapsed plan that keeps its reach until a nightly job notices is
    #: reach nobody paid for.
    plan_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # "Show businesses when I was last online."
    #
    # A PLAIN BOOLEAN, deliberately -- unlike offers_delivery next door,
    # which had to become tri-state. The difference: FALSE here is a
    # real, safe, complete answer ("don't show my activity") that
    # asserts nothing about the supplier to anyone. offers_delivery's
    # false asserted "this supplier does not deliver", which is a claim
    # nobody had made. A privacy switch defaulting to private states
    # nothing on the person's behalf, so two states are genuinely
    # enough.
    #
    # Defaults FALSE: same cautious opt-in as share_contact_details and
    # VisibleImageSource.NONE -- being visible is always the choice,
    # never the default.
    show_last_active = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    # "Show businesses my track record" -- the connections/orders/repeat
    # buyer figures on the brand profile.
    #
    # DEFAULTS TRUE, unlike show_last_active right above it, and the
    # difference is deliberate. Every PUBLIC track-record figure is a
    # count that only grows and is hidden entirely at zero, so there is
    # no arrangement of the data that can make a supplier look bad by
    # default -- a new supplier simply shows fewer rows. Defaulting this
    # OFF would hide a feature that only ever helps the supplier, from
    # every supplier who never finds the setting.
    #
    # The harsher figures (acceptance rate, reply time, cancellations)
    # are deliberately NOT in the public set at all -- they live on the
    # supplier's own profile, where they're actionable rather than
    # punishing. See supplier_profile_routes._performance_stats.
    show_track_record = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())

    verification_status = db.Column(
        db.Enum(SupplierVerificationStatus, name="supplier_verification_status", schema="supplier"),
        nullable=False,
        default=SupplierVerificationStatus.UNVERIFIED,
    )

    # HOW FAR ALONG THE REMINDER LADDER THIS SUPPLIER IS, while they
    # wait to be verified (V2_12 Phase 1). 0 = nothing sent, 3 = the
    # ladder is finished and we stop -- a platform that emails forever
    # about its OWN pending decision is nagging somebody about work
    # they cannot do anything about.
    #
    # sent_at DOUBLES AS THE CLOCK: null means nothing has been sent
    # and the sweep falls back to created_at, which is what stops every
    # existing supplier receiving all three emails in the first run
    # after deploy. Reset by approve() and revoke() so the wait is
    # always measured from the moment the curtain actually closed.
    verification_reminder_stage = db.Column(
        db.SmallInteger, nullable=False, default=0, server_default="0"
    )
    verification_reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Normalized, indexed, search-only -- see module docstring.
    normalized_phone = db.Column(db.String(20), nullable=True)
    normalized_email = db.Column(db.String(255), nullable=True)

    # A business-specific image, distinct from the PERSONAL photo on
    # auth.users -- a supplier can be shown as themselves or as their
    # business, their choice (visible_image_source below).
    business_image_url = db.Column(db.String(500), nullable=True)
    # A SEPARATE, wide/banner-style image -- deliberately its own
    # column, not a second use of business_image_url. These are two
    # different UI concepts (a square/circular identity photo vs. a
    # wide brand-showcase banner shown at the top of the profile) --
    # reuse was considered and explicitly rejected in favour of a
    # genuinely separate field during the Relationship Intelligence
    # planning round. Same real/mock boundary as business_image_url --
    # the column exists now, the frontend upload flow is mock-backed
    # until a real upload-session backend exists (see
    # fileRepository.ts's own docstring on that discipline).
    cover_image_url = db.Column(db.String(500), nullable=True)
    visible_image_source = db.Column(
        db.Enum(VisibleImageSource, name="visible_image_source", schema="supplier"),
        nullable=False,
        default=VisibleImageSource.NONE,
    )
    photo_visibility = db.Column(
        db.Enum(PhotoVisibility, name="photo_visibility", schema="supplier"),
        nullable=False,
        default=PhotoVisibility.CONNECTIONS,
    )

    # Real contact channels a supplier can choose to share with
    # CONNECTED businesses only -- deliberately no EVERYONE tier here,
    # unlike PhotoVisibility above. A photo shown in bare search
    # results is one kind of exposure; a phone number or email address
    # is a materially different, more sensitive one, and this domain's
    # own architecture review agreed connected-only is the right
    # (and only) gate for this data, not a wider opt-in. All three
    # nullable -- a supplier who hasn't filled one in has nothing to
    # show regardless of share_contact_details below.
    whatsapp_number = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    tiktok_handle = db.Column(db.String(100), nullable=True)
    # ONE combined gate, not one per field -- a supplier who wants to
    # share WhatsApp but not email accomplishes that by simply leaving
    # email blank, rather than needing three separate switches to
    # reason about. Defaults False -- same cautious "nothing shows
    # until explicitly opted in" philosophy as
    # VisibleImageSource.NONE's own default just above.
    share_contact_details = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())

    # The next number products/algorithms/sku_generator.py will issue
    # for this supplier -- starts at 1, so the first auto-generated SKU
    # is SKU-0001. Deliberately its own dedicated counter, never
    # derived by counting or parsing existing products' SKU text (a
    # supplier's own custom-typed SKU could be anything and must never
    # influence what number comes next). Only ever moves forward, never
    # decremented or reused, even if a product is later deleted.
    next_sku_sequence = db.Column(db.Integer, nullable=False, default=1, server_default="1")

    def to_search_result_dict(self) -> dict:
        """The PRIVACY-NARROWED shape for a search result row -- see
        file.txt §4: enough to recognise the supplier, never the full
        stored record. Deliberately does NOT reuse to_public_dict-style
        full serialization; this method exists specifically so nobody
        accidentally widens a search response by generalizing it later.

        No longer takes matched_field/masked_identifier -- search is
        name/business-name only now (phone/email exact-match search
        was removed, see connections' _common._dispatch_search
        docstring for the full reasoning). Those two fields would only
        ever have been "NAME"/"" once that was true, so rather than
        keep two permanently-constant fields around, the shape was
        simplified to drop them entirely."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category,
            "location": self.location,
            "verificationStatus": self.verification_status.value if self.verification_status else None,
        }

    def to_profile_preview_dict(self, connection_status: str, visible_photo_url: str | None = None) -> dict:
        """One level deeper than a search result (file.txt §4's
        "supplier profile" step) -- still narrow, still not the
        supplier's full record. connection_status AND
        visible_photo_url are both passed in rather than resolved
        here, since both depend on data this model doesn't own
        (ConnectionRequest, and auth.users.profile_image_url) --
        same reasoning connection_status's own docstring already
        established, extended to the photo. Deliberately NOT added to
        to_search_result_dict above -- a photo is a step further than
        bare search results should expose, even under EVERYONE
        visibility; the profile preview is where richer identity
        information belongs."""
        return {
            "id": str(self.id),
            "businessName": self.business_name,
            "category": self.category,
            "location": self.location,
            "verificationStatus": self.verification_status.value if self.verification_status else None,
            # Month + year, e.g. "March 2026" -- the business-facing
            # brand profile shows "On TruConnect since <this>". Month
            # precision, deliberately never the day: enough to signal
            # "established, not brand new" without fingerprinting the
            # exact signup moment (file.txt §4's privacy framing still
            # applies -- it just lands at month, not year, now).
            "memberSince": self.created_at.strftime("%B %Y") if self.created_at else None,
            "description": self.description,
            "connectionStatus": connection_status,
            "photoUrl": visible_photo_url,
        }
