#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build website nhakhoaavadental.vn (site tĩnh, deploy thẳng lên Vercel).

Cách dùng:
    pip install pillow          # chỉ cần 1 lần
    python3 build.py

Script sẽ:
  1. Quét 4 thư mục ảnh ca thực tế, tự đổi tên / tạo ảnh webp + thumb cho ảnh mới upload.
  2. Sinh lại toàn bộ các trang HTML, sitemap.xml, robots.txt.
Trang thư viện ảnh của dịch vụ nào chưa có ảnh sẽ tự đặt noindex và không đưa vào sitemap.
"""
import html
import json
import re
import shutil
import sys
import unicodedata
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://nhakhoaavadental.vn"
TODAY = datetime.date.today().isoformat()
ASSET_V = "20261102"

PHONE = "028.2206.6666"
PHONE_TEL = "02822066666"
ZALO = "https://zalo.me/0388888272"
ADDRESS_SHORT = "283/91 Cách Mạng Tháng 8, Phường Hòa Hưng, Quận 10, TP.HCM"

# ---------------------------------------------------------------------------
# BẢNG GIÁ - sửa số ở đây là bảng giá toàn site cập nhật theo.
# Để None = hiển thị "Báo giá sau khi thăm khám".
# ---------------------------------------------------------------------------
PRICE_OTHER = [
    # (dịch vụ, mô tả, giá)
    ("Trồng răng Implant", "Mỗi trụ implant, chưa gồm răng sứ phục hình", None),
    ("Ghép xương / nâng xoang (nếu cần)", "Chỉ định khi xương hàm không đủ điều kiện", None),
    ("Bọc răng sứ", "Tính theo từng răng, tùy loại sứ", None),
    ("Mặt dán sứ (veneer)", "Tính theo từng răng", None),
    ("Trám răng thẩm mỹ", "Tính theo từng răng / từng mặt răng", None),
]

# ---------------------------------------------------------------------------
# DỊCH VỤ + THƯ MỤC ẢNH
# ---------------------------------------------------------------------------
SERVICES = [
    dict(key="nieng-rang", name="Niềng răng", url="/nieng-rang/", icon="fa-teeth",
         folder="nieng-rang", prefix="nieng-rang-quan-10-truoc-sau",
         gallery_url="/hinh-anh-nieng-rang/", gallery_file="hinh-anh-nieng-rang.html",
         short="Chỉnh nha mắc cài kim loại, mắc cài sứ, Invisalign. Bác sĩ chuyên khoa trực tiếp điều trị.",
         alts=["Ca niềng răng quận 10 trước và sau điều trị tại Nha khoa AVA, ca {n}",
               "Hình ảnh trước và sau khi niềng răng tại Nha khoa AVA Quận 10 TPHCM, ca {n}"]),
    dict(key="trong-rang-implant", name="Trồng răng Implant", url="/trong-rang-implant/", icon="fa-tooth",
         folder="trong-rang-implant", prefix="trong-rang-implant-quan-10-truoc-sau",
         gallery_url="/hinh-anh-trong-rang-implant/", gallery_file="hinh-anh-trong-rang-implant.html",
         short="Phục hồi răng đã mất bằng trụ implant, ăn nhai chắc chắn và thẩm mỹ.",
         alts=["Ca trồng răng Implant quận 10 trước và sau điều trị tại Nha khoa AVA, ca {n}",
               "Hình ảnh trước và sau khi trồng răng Implant tại Nha khoa AVA Quận 10 TPHCM, ca {n}"]),
    dict(key="rang-su", name="Răng sứ", url="/rang-su/", icon="fa-crown",
         folder="rang-su", prefix="rang-su-quan-10-truoc-sau",
         gallery_url="/hinh-anh-rang-su/", gallery_file="hinh-anh-rang-su.html",
         short="Bọc răng sứ, mặt dán sứ để cải thiện màu sắc, hình dáng và chức năng ăn nhai.",
         alts=["Ca bọc răng sứ quận 10 trước và sau điều trị tại Nha khoa AVA, ca {n}",
               "Hình ảnh trước và sau khi làm răng sứ tại Nha khoa AVA Quận 10 TPHCM, ca {n}"]),
    dict(key="tram-rang-tham-my", name="Trám răng thẩm mỹ", url="/tram-rang-tham-my/", icon="fa-wand-magic-sparkles",
         folder="tram-rang-tham-my", prefix="tram-rang-tham-my-quan-10-truoc-sau",
         gallery_url="/hinh-anh-tram-rang-tham-my/", gallery_file="hinh-anh-tram-rang-tham-my.html",
         short="Phục hồi răng sâu, mẻ bằng vật liệu cùng màu răng, ít xâm lấn, thường xong trong một buổi.",
         alts=["Ca trám răng thẩm mỹ quận 10 trước và sau điều trị tại Nha khoa AVA, ca {n}",
               "Hình ảnh trước và sau khi trám răng thẩm mỹ tại Nha khoa AVA Quận 10 TPHCM, ca {n}"]),
]
SVC = {s["key"]: s for s in SERVICES}

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
IMG_DIR = ROOT / "assets" / "images"


def slugify(s):
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def natural_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s.lower())]


# ---------------------------------------------------------------------------
# XỬ LÝ ẢNH
# ---------------------------------------------------------------------------
def process_folder(svc):
    """Chuẩn hóa ảnh mới upload: đổi tên, tạo webp (rộng tối đa 900px) + thumb 420px."""
    d = IMG_DIR / svc["folder"]
    d.mkdir(parents=True, exist_ok=True)
    pre = svc["prefix"]
    pat = re.compile(rf"^{re.escape(pre)}-(\d+)(-thumb)?$")
    files = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT]
    nums = [int(m.group(1)) for p in files if (m := pat.match(p.stem))]
    nxt = max(nums) if nums else 0
    raws = [p for p in files if not pat.match(p.stem)]
    if not raws:
        return
    try:
        from PIL import Image, ImageOps
    except ImportError:
        sys.exit("Thiếu Pillow. Chạy: pip install pillow")
    backup = d / "_goc"
    backup.mkdir(exist_ok=True)
    groups = {}
    for p in sorted(raws, key=lambda x: natural_key(x.name)):
        groups.setdefault(slugify(p.stem), []).append(p)
    for _, grp in groups.items():
        src = max(grp, key=lambda x: x.stat().st_size)
        nxt += 1
        name = f"{pre}-{nxt:02d}" if nxt < 100 else f"{pre}-{nxt}"
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert("RGB")  # bỏ EXIF
        full = im.copy()
        if full.width > 900:
            full = full.resize((900, round(full.height * 900 / full.width)), Image.LANCZOS)
        full.save(d / f"{name}.webp", "WEBP", quality=80, method=6)
        th = im.copy()
        if th.width > 420:
            th = th.resize((420, round(th.height * 420 / th.width)), Image.LANCZOS)
        th.save(d / f"{name}-thumb.webp", "WEBP", quality=78, method=6)
        th.save(d / f"{name}-thumb.jpg", "JPEG", quality=80, optimize=True)
        for p in grp:
            shutil.move(str(p), str(backup / p.name))
        print(f"  [{svc['folder']}] {src.name} -> {name}")


def collect_cases(svc):
    d = IMG_DIR / svc["folder"]
    pat = re.compile(rf"^{re.escape(svc['prefix'])}-(\d+)(-thumb)?$")
    found = {}
    if d.exists():
        for p in d.iterdir():
            m = pat.match(p.stem) if p.is_file() and p.suffix.lower() in IMG_EXT else None
            if not m:
                continue
            n = int(m.group(1))
            found.setdefault(n, {})[("thumb_" if m.group(2) else "full_") + p.suffix.lower().lstrip(".")] = p.name
    cases = []
    for n in sorted(found):
        f = found[n]
        full = f.get("full_webp") or f.get("full_jpg") or f.get("full_jpeg") or f.get("full_png")
        thumb_webp = f.get("thumb_webp")
        thumb_jpg = f.get("thumb_jpg")
        if not full or not (thumb_webp or thumb_jpg):
            continue
        base = f"/assets/images/{svc['folder']}/"
        tw, th_ = 420, 583
        try:
            from PIL import Image
            with Image.open(d / (thumb_webp or thumb_jpg)) as im:
                tw, th_ = im.size
        except Exception:
            pass
        cases.append(dict(n=n, full=base + full,
                          thumb_webp=base + thumb_webp if thumb_webp else None,
                          thumb_jpg=base + (thumb_jpg or thumb_webp), w=tw, h=th_))
    return cases


def gallery_item(c, svc, idx, eager=False, hidden=False, tag=None):
    alt = svc["alts"][idx % 2].format(n=f"{c['n']:02d}")
    src = f'<source srcset="{c["thumb_webp"]}" type="image/webp">' if c["thumb_webp"] else ""
    more = " data-more hidden" if hidden else ""
    tag = tag or f"Ca {c['n']:02d}"
    return (f'<div class="gallery-item"{more} data-full="{c["full"]}"><div class="thumb-frame"><picture>{src}'
            f'<img src="{c["thumb_jpg"]}" alt="{html.escape(alt)}" loading="{"eager" if eager else "lazy"}" '
            f'width="{c["w"]}" height="{c["h"]}"></picture></div><span class="tag">{tag}</span></div>')


# ---------------------------------------------------------------------------
# LAYOUT CHUNG
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=True)


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + "\n</script>"


def dentist_ld():
    return {
        "@context": "https://schema.org",
        "@type": ["Dentist", "MedicalBusiness"],
        "@id": f"{SITE}/#dentist",
        "name": "Nha khoa AVA (Công Ty TNHH Nha Khoa Thẩm Mỹ AVA)",
        "alternateName": "Nha khoa quận 10 AVA",
        "legalName": "Công Ty TNHH Nha Khoa Thẩm Mỹ AVA",
        "url": SITE + "/",
        "image": f"{SITE}/assets/images/logo/og-logo.png",
        "logo": f"{SITE}/assets/images/logo/ava-logo.png",
        "telephone": "+842822066666",
        "taxID": "0312093828",
        "areaServed": [{"@type": "AdministrativeArea", "name": "Quận 10"},
                       {"@type": "City", "name": "TP. Hồ Chí Minh"}],
        "identifier": {"@type": "PropertyValue", "name": "Giấy phép hoạt động", "propertyID": "GPHĐ",
                       "value": "04405/SYT-GPHĐ"},
        "contactPoint": [{"@type": "ContactPoint", "telephone": t, "contactType": "reservations", "areaServed": "VN"}
                         for t in ("+842822066666", "+842866862222", "+842862887777", "+842822297297")],
        "address": {"@type": "PostalAddress", "streetAddress": "283/91 Cách Mạng Tháng 8, Phường Hòa Hưng",
                    "addressLocality": "Quận 10", "addressRegion": "TP. Hồ Chí Minh", "addressCountry": "VN"},
        "geo": {"@type": "GeoCoordinates", "latitude": 10.777462342977538, "longitude": 106.67944161217169},
        "hasMap": "https://g.page/nhakhoava",
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                       "opens": "08:00", "closes": "17:00"}],
        "sameAs": ["https://www.facebook.com/NhaKhoaAVA/", "https://twitter.com/NhaKhoaAVAdenta",
                   "https://www.youtube.com/@NhaKhoaAVA"],
        "medicalSpecialty": "Dentistry",
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Dịch vụ nha khoa tại Nha khoa AVA Quận 10",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "MedicalProcedure", "name": s["name"],
                                                                   "url": SITE + s["url"]}} for s in SERVICES]},
        "employee": {"@type": "Person", "@id": f"{SITE}/bac-si-pham-viet-hung/#person", "name": "Phạm Việt Hùng",
                     "honorificPrefix": "BS.", "jobTitle": "Bác sĩ Chuyên khoa Răng Hàm Mặt",
                     "identifier": {"@type": "PropertyValue", "name": "Chứng chỉ hành nghề", "propertyID": "CCHN",
                                    "value": "008280/HCM-CCHN"}},
    }


def website_ld():
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE + "/",
            "name": "Nha khoa quận 10 – Nha khoa AVA", "inLanguage": "vi-VN",
            "publisher": {"@id": f"{SITE}/#dentist"}}


def breadcrumb_ld(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
                                for i, (n, u) in enumerate(trail)]}


def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
                           for q, a in faqs]}


def head(title, desc, path, lds=(), robots="index, follow", og_image="/assets/images/logo/og-logo.png"):
    url = SITE + path
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<meta name="author" content="Nha khoa AVA">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="vi_VN">
<meta property="og:site_name" content="Nha khoa AVA">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}{og_image}">
<meta name="twitter:site" content="@NhaKhoaAVAdenta">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/images/logo/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/css/style.css?v={ASSET_V}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
{chr(10).join(jsonld(x) for x in lds)}
</head>
<body>
"""


ARTICLES = [
    ("/nieng-rang-tra-gop-dieu-kien-thu-tuc/", "Niềng răng trả góp: điều kiện, thủ tục",
     "Niềng răng trả góp hoạt động thế nào, cần chuẩn bị gì và những điều phải hỏi rõ trước khi đăng ký.",
     "nieng-rang-quan-10-truoc-sau-13"),
    ("/nieng-rang-mac-cai-hay-invisalign/", "Mắc cài hay Invisalign?",
     "So sánh mắc cài kim loại, mắc cài sứ và Invisalign về thẩm mỹ, sinh hoạt và chi phí.",
     "nieng-rang-quan-10-truoc-sau-23"),
    ("/nieng-rang-bao-lau-co-dau-khong/", "Niềng răng bao lâu, có đau không?",
     "Thời gian niềng răng, cảm giác đau, ăn uống, vệ sinh và hàm duy trì sau khi tháo niềng.",
     "nieng-rang-quan-10-truoc-sau-106"),
]


def header(active=""):
    svc_cards = "".join(
        f'<a class="nav-article-card" href="{s["url"]}"><span class="nac-icon"><i class="fa-solid {s["icon"]}"></i></span>'
        f'<span><span class="nac-title">{s["name"]} quận 10</span><span class="nac-desc">{esc(s["short"])}</span></span></a>'
        for s in SERVICES)
    art_cards = "".join(
        f'<a class="nav-article-card" href="{u}"><picture><source srcset="/assets/images/nieng-rang/{img}-thumb.webp" type="image/webp">'
        f'<img src="/assets/images/nieng-rang/{img}-thumb.jpg" alt="{esc(t)} – Nha khoa AVA Quận 10" loading="lazy" width="104" height="66" style="object-position:top"></picture>'
        f'<span><span class="nac-title">{t}</span><span class="nac-desc">{esc(d)}</span></span></a>'
        for u, t, d, img in ARTICLES)
    return f"""<header class="site-header">
  <div class="policy-strip"><i class="fa-solid fa-circle-info"></i> AVA <strong>không tư vấn qua điện thoại / trực tuyến</strong> — Đến trực tiếp phòng khám để được tư vấn &amp; chụp phim <strong>MIỄN PHÍ</strong></div>
  <div class="header-row">
    <a href="/" class="brand">
      <img src="/assets/images/logo/ava-logo.png" alt="Logo Nha khoa AVA - Nha khoa quận 10" width="40" height="41">
      <span class="brand-text"><strong>Nha khoa AVA</strong><span>Nha khoa quận 10 · TP.HCM</span></span>
    </a>
    <nav class="main-nav" aria-label="Điều hướng chính">
      <div class="nav-item has-dropdown">
        <button class="nav-dd-toggle" type="button" aria-expanded="false" aria-haspopup="true">Dịch vụ <i class="fa-solid fa-chevron-down"></i></button>
        <div class="nav-dropdown"><div class="nav-dropdown-inner">{svc_cards}</div></div>
      </div>
      <a href="/hinh-anh-truoc-sau/">Hình ảnh</a>
      <a href="/bang-gia/">Bảng giá</a>
      <div class="nav-item has-dropdown">
        <button class="nav-dd-toggle" type="button" aria-expanded="false" aria-haspopup="true">Kiến thức <i class="fa-solid fa-chevron-down"></i></button>
        <div class="nav-dropdown"><div class="nav-dropdown-inner">{art_cards}</div></div>
      </div>
      <a href="/gioi-thieu/">Giới thiệu</a>
      <a href="/#faq">Hỏi đáp</a>
      <a href="/#lien-he">Liên hệ</a>
    </nav>
    <div class="header-actions">
      <a class="header-hotline" href="tel:{PHONE_TEL}"><i class="fa-solid fa-phone-volume"></i> <span>{PHONE}</span></a>
      <button class="nav-toggle" aria-label="Mở menu" aria-expanded="false"><i class="fa-solid fa-bars"></i></button>
    </div>
  </div>
</header>
"""


def footer():
    links = "".join(f'<li><a href="{s["url"]}">{s["name"]} quận 10</a></li>' for s in SERVICES)
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand"><img src="/assets/images/logo/ava-logo.png" alt="Logo Nha khoa AVA"><strong>Nha khoa AVA</strong></div>
        <p>Nha khoa thẩm mỹ AVA tại Quận 10, TP. Hồ Chí Minh: niềng răng, trồng răng Implant, răng sứ, trám răng thẩm mỹ và các dịch vụ chăm sóc răng miệng.</p>
      </div>
      <div>
        <h5>Dịch vụ</h5>
        <ul>{links}</ul>
      </div>
      <div>
        <h5>Liên hệ</h5>
        <ul>
          <li>{ADDRESS_SHORT.replace(", Phường Hòa Hưng", "")}</li>
          <li><a href="tel:{PHONE_TEL}">{PHONE}</a></li>
          <li><a href="{ZALO}">Zalo 038 888 8272</a></li>
          <li><a href="/bang-gia/">Bảng giá</a> · <a href="/hinh-anh-truoc-sau/">Hình ảnh</a></li>
        </ul>
      </div>
      <div>
        <h5>Theo dõi</h5>
        <ul>
          <li><a href="https://www.facebook.com/NhaKhoaAVA/" target="_blank" rel="noopener">Facebook</a></li>
          <li><a href="http://www.youtube.com/@NhaKhoaAVA" target="_blank" rel="noopener">Youtube</a></li>
          <li><a href="https://twitter.com/NhaKhoaAVAdenta" target="_blank" rel="noopener">Twitter</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 Công Ty TNHH Nha Khoa Thẩm Mỹ AVA · MST 0312093828 · GPHĐ 04405/SYT-GPHĐ</span>
      <span>{ADDRESS_SHORT}</span>
    </div>
  </div>
</footer>

<div class="float-sidebar" aria-label="Liên hệ nhanh">
  <a href="tel:{PHONE_TEL}" class="fs-hotline" aria-label="Gọi hotline"><span class="fs-ping"></span><i class="fa-solid fa-phone"></i><span class="fs-label">Gọi Hotline</span></a>
  <a href="{ZALO}" target="_blank" rel="noopener" class="fs-zalo" aria-label="Chat Zalo"><img src="/assets/images/logo/zalo-icon-128.png" alt="Zalo"><span class="fs-label">Chat Zalo</span></a>
  <a href="https://m.me/NhaKhoaAVA" target="_blank" rel="noopener" class="fs-messenger" aria-label="Chat Facebook Messenger"><i class="fa-brands fa-facebook-messenger" style="font-family:'Font Awesome 6 Brands'"></i><span class="fs-label">Chat Facebook</span></a>
  <button class="fs-top" aria-label="Lên đầu trang"><i class="fa-solid fa-arrow-up"></i></button>
</div>

<div class="lightbox">
  <button class="lightbox-close" aria-label="Đóng"><i class="fa-solid fa-xmark"></i></button>
  <img src="" alt="">
  <div class="lightbox-caption"></div>
</div>

<script src="/assets/js/main.js?v={ASSET_V}"></script>
</body>
</html>
"""


def cta_banner(title="Đặt lịch thăm khám tại Nha khoa AVA quận 10",
               text="Đến trực tiếp phòng khám để được bác sĩ thăm khám, chụp phim kiểm tra miễn phí và tư vấn phương án phù hợp."):
    return f"""
<section class="section">
  <div class="container">
    <div class="cta-banner">
      <div><h2>{title}</h2><p>{text}</p></div>
      <div class="cta-actions">
        <a href="/#lien-he" class="btn btn-primary"><i class="fa-solid fa-calendar-check"></i> Đặt lịch ngay</a>
        <a href="{ZALO}" target="_blank" rel="noopener" class="btn btn-ghost-light"><img src="/assets/images/logo/zalo-icon-64.png" alt="Zalo" class="ico-zalo"> Chat Zalo</a>
      </div>
    </div>
  </div>
</section>
"""


def faq_block(faqs, title, prefix="faq", alt=True):
    items = ""
    for i, (q, a) in enumerate(faqs, 1):
        items += (f'<div class="faq-item"><h3 class="faq-h"><button class="faq-q" aria-expanded="false" aria-controls="{prefix}-a-{i}">'
                  f'{q} <i class="fa-solid fa-plus"></i></button></h3><div class="faq-a" id="{prefix}-a-{i}" role="region">'
                  f'<div class="faq-a-inner">{a}</div></div></div>\n')
    return f"""
<section class="section{' section-alt' if alt else ''}" id="faq">
  <div class="container">
    <div class="section-head"><span class="kicker"><span class="dot"></span>Câu hỏi thường gặp</span><h2>{title}</h2></div>
    <div class="faq-list">
{items}    </div>
  </div>
</section>
"""


def page_hero(trail, kicker, h1, sub, ctas=True):
    crumbs = ""
    for i, (n, u) in enumerate(trail):
        crumbs += ("<span>/</span>" if i else "") + (f'<a href="{u}">{n}</a>' if i < len(trail) - 1 else f"<span>{n}</span>")
    btn = (f'<div class="hero-cta-row" style="margin-top:22px"><a href="/#lien-he" class="btn btn-primary"><i class="fa-solid fa-calendar-check"></i> Đặt lịch khám &amp; tư vấn</a>'
           f'<a href="tel:{PHONE_TEL}" class="btn btn-outline"><i class="fa-solid fa-phone"></i> Gọi Hotline</a></div>') if ctas else ""
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="breadcrumb">{crumbs}</div>
    <span class="kicker"><span class="dot"></span>{kicker}</span>
    <h1>{h1}</h1>
    <p class="hero-sub">{sub}</p>
    {btn}
  </div>
</section>
"""


def process_block(steps, title, kicker="Quy trình", intro=""):
    st = "".join(f'<div class="process-step"><div class="step-num">{i}</div><h4>{h}</h4><p>{p}</p></div>'
                 for i, (h, p) in enumerate(steps, 1))
    return f"""
<section class="section section-alt">
  <div class="container">
    <div class="section-head"><span class="kicker"><span class="dot"></span>{kicker}</span><h2>{title}</h2>{intro}</div>
    <div class="process-track">{st}</div>
  </div>
</section>
"""


def price_fmt(p):
    return p if p else "Báo giá sau khi thăm khám"


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")
    print("  wrote", rel)


# ---------------------------------------------------------------------------
# NỘI DUNG DỊCH VỤ
# ---------------------------------------------------------------------------
LI = '<li><i class="fa-solid fa-circle-check"></i> {}</li>'


def check_list(items):
    return '<ul class="check-list">' + "".join(LI.format(i) for i in items) + "</ul>"


CONTENT = {}

CONTENT["nieng-rang"] = dict(
    title="Niềng Răng Quận 10, TPHCM | Mắc Cài, Invisalign – Nha Khoa AVA",
    desc="Niềng răng quận 10 tại Nha khoa AVA: bác sĩ chuyên khoa trực tiếp điều trị, mắc cài kim loại từ 20 triệu, mắc cài sứ, Invisalign. Khám & chụp phim miễn phí.",
    kicker="Niềng răng (chỉnh nha)",
    h1="Niềng răng quận 10, TPHCM – bác sĩ chuyên khoa trực tiếp điều trị",
    sub="Mắc cài kim loại, mắc cài sứ và Invisalign tại Nha khoa AVA. Bạn được thăm khám, chụp phim kiểm tra miễn phí trước khi chọn phương án.",
    lead="Nha khoa AVA nhận niềng răng (chỉnh nha) tại Quận 10, TPHCM với bác sĩ chuyên khoa Răng Hàm Mặt trực tiếp thăm khám, lên kế hoạch và theo dõi suốt quá trình điều trị. Bạn được khám và chụp phim kiểm tra miễn phí trước khi chọn mắc cài kim loại, mắc cài sứ hay Invisalign.",
    sections=[
        ("Những trường hợp thường cần niềng răng", "<p>Niềng răng giúp đưa răng và khớp cắn về vị trí hài hòa hơn, vừa cải thiện thẩm mỹ vừa giúp việc ăn nhai và vệ sinh răng miệng dễ dàng hơn. Bạn có thể cân nhắc niềng răng khi gặp một trong các tình trạng sau:</p>"
         + check_list(["Răng mọc lệch lạc, chen chúc, xoay hoặc chồng lên nhau.",
                       "Răng thưa, hở kẽ hoặc có khoảng trống giữa các răng.",
                       "Khớp cắn bất thường: cắn sâu, cắn hở, cắn chéo, hô hoặc móm (mức độ do bác sĩ đánh giá).",
                       "Muốn cải thiện nụ cười và có hàm răng đều, dễ làm sạch hơn."])
         + "<p>Không phải ai cũng cần niềng. Phương án phù hợp được bác sĩ quyết định dựa trên thăm khám lâm sàng và phim chụp, bao gồm cả khả năng không cần niềng hoặc kết hợp với dịch vụ khác.</p>"),
    ],
    after_sections="PRICE_NIENG",
    steps=[("Khám &amp; chụp phim", "Bác sĩ đánh giá tình trạng răng, xương hàm, khớp cắn. Khám và chụp phim kiểm tra miễn phí."),
           ("Lập kế hoạch &amp; báo giá", "Thống nhất phương pháp, cấp độ ca và chi phí dự kiến sau khi có kết quả thăm khám."),
           ("Gắn khí cụ", "Gắn mắc cài hoặc bắt đầu bộ khay trong suốt theo kế hoạch đã thống nhất."),
           ("Tái khám &amp; duy trì", "Tái khám định kỳ để điều chỉnh; sau khi tháo niềng cần đeo hàm duy trì để giữ kết quả.")],
    steps_title="Quy trình niềng răng tại AVA",
    tail="<h2>Niềng răng mất bao lâu, có đau không?</h2><p>Nhiều trường hợp cần khoảng 1,5 đến 3 năm, tùy mức độ sai lệch và sự hợp tác của người niềng. Bạn có thể thấy ê nhức nhẹ trong vài ngày sau khi gắn khí cụ hoặc điều chỉnh. Chi tiết xem bài <a href=\"/nieng-rang-bao-lau-co-dau-khong/\">Niềng răng bao lâu, có đau không?</a> và <a href=\"/nieng-rang-mac-cai-hay-invisalign/\">Mắc cài hay Invisalign?</a>. Nếu quan tâm đến việc chia nhỏ chi phí, tham khảo <a href=\"/nieng-rang-tra-gop-dieu-kien-thu-tuc/\">niềng răng trả góp: điều kiện, thủ tục</a>.</p>",
    faqs=[
        ("Niềng răng quận 10 giá bao nhiêu?", "Tại Nha khoa AVA, niềng răng mắc cài kim loại có giá tham khảo từ 20 triệu đồng (cấp độ 1); mắc cài sứ và Invisalign cao hơn. Mức giá cụ thể phụ thuộc cấp độ ca do bác sĩ đánh giá sau khi thăm khám, xem chi tiết tại <a href=\"/bang-gia/\">bảng giá</a>."),
        ("Nên niềng mắc cài hay Invisalign?", "Mắc cài phù hợp với nhiều mức độ sai lệch và có chi phí thấp hơn; Invisalign thẩm mỹ, tháo lắp được nhưng đòi hỏi tự giác đeo đủ thời gian và không phù hợp với mọi ca. Bác sĩ sẽ tư vấn sau khi khám. Xem thêm bài <a href=\"/nieng-rang-mac-cai-hay-invisalign/\">Mắc cài hay Invisalign?</a>."),
        ("Niềng xong có phải đeo hàm duy trì không?", "Có. Sau khi tháo niềng, răng vẫn có xu hướng xô lệch trở lại nên bạn cần đeo khí cụ duy trì theo chỉ định của bác sĩ để giữ kết quả lâu dài."),
        ("Trẻ em có niềng răng được không?", "Có thể chỉnh hình răng cho trẻ ở giai đoạn thích hợp (thường 8–12 tuổi cho giai đoạn 1 và 12–14 tuổi cho giai đoạn 2). Thời điểm và phương pháp do bác sĩ quyết định sau khi thăm khám."),
        ("Địa chỉ niềng răng của Nha khoa AVA ở đâu?", "Nha khoa AVA tại 283/91 Cách Mạng Tháng 8, Phường Hòa Hưng, Quận 10, TP.HCM, mở cửa Thứ 2 – Thứ 7 (8:00 – 17:00)."),
    ],
    related=["trong-rang-implant", "rang-su", "tram-rang-tham-my"],
)

CONTENT["trong-rang-implant"] = dict(
    title="Trồng Răng Implant Quận 10, TPHCM | Phục Hồi Răng Mất – Nha Khoa AVA",
    desc="Trồng răng Implant quận 10 tại Nha khoa AVA: khám, chụp phim đánh giá xương hàm miễn phí, tư vấn phương án phục hồi răng mất. 283/91 Cách Mạng Tháng 8, Q.10.",
    kicker="Trồng răng Implant",
    h1="Trồng răng Implant quận 10, TPHCM – phục hồi răng đã mất",
    sub="Thay thế chân răng đã mất bằng trụ implant và phục hình răng sứ phía trên. Bạn được khám và chụp phim đánh giá miễn phí trước khi bác sĩ tư vấn phương án.",
    lead="Trồng răng Implant là phương pháp đặt một trụ (thường làm bằng titanium) vào xương hàm để thay cho chân răng đã mất, sau đó gắn răng sứ lên trên. Tại Nha khoa AVA, bạn được bác sĩ thăm khám và chụp phim kiểm tra miễn phí để đánh giá xương hàm, nướu và tình trạng răng miệng trước khi tư vấn phương án phù hợp.",
    sections=[
        ("Implant phù hợp với những trường hợp nào?",
         "<p>Implant thường được cân nhắc khi bạn bị mất một răng, nhiều răng hoặc mất răng toàn hàm và muốn phục hồi khả năng ăn nhai. So với cầu răng sứ, implant không cần mài các răng thật bên cạnh để làm trụ đỡ.</p>"
         "<p>Tuy nhiên, implant không phù hợp với mọi người. Xương hàm cần đủ thể tích và chất lượng, nướu cần khỏe, và một số bệnh lý toàn thân hoặc thói quen (như hút thuốc lá) có thể ảnh hưởng đến kết quả. Bác sĩ sẽ đánh giá cụ thể qua thăm khám và phim chụp, đồng thời cho biết có cần xử lý thêm (điều trị viêm nướu, ghép xương...) trước khi cấy hay không.</p>"),
        ("So sánh implant với các cách phục hồi răng mất",
         '<div class="price-table-wrap"><table class="price-table"><thead><tr><th>Tiêu chí</th><th>Implant</th><th>Cầu răng sứ</th><th>Hàm tháo lắp</th></tr></thead><tbody>'
         "<tr><td>Cách thực hiện</td><td>Đặt trụ vào xương hàm, gắn răng sứ lên trụ</td><td>Mài hai răng bên cạnh làm trụ, bắc cầu răng sứ</td><td>Hàm có móc hoặc nền nhựa, tháo ra vào hằng ngày</td></tr>"
         "<tr><td>Mài răng thật bên cạnh</td><td>Không</td><td>Có</td><td>Thường không</td></tr>"
         "<tr><td>Phẫu thuật</td><td>Có (tiểu phẫu tại chỗ)</td><td>Không</td><td>Không</td></tr>"
         "<tr><td>Thời gian hoàn thiện</td><td>Thường kéo dài hơn do cần chờ tích hợp xương</td><td>Ngắn hơn</td><td>Ngắn nhất</td></tr>"
         "</tbody></table></div><p class=\"price-note\">Bảng so sánh mang tính tổng quát. Lựa chọn phù hợp phụ thuộc tình trạng xương hàm, nướu và mong muốn của bạn.</p>"),
        ("Chi phí trồng răng Implant",
         "<p>Chi phí phụ thuộc vào số lượng răng cần phục hồi, loại trụ implant và răng sứ phục hình, cũng như việc có cần ghép xương hoặc nâng xoang hay không. Vì vậy phòng khám báo giá cụ thể sau khi bác sĩ thăm khám và có kết quả phim. Xem thêm tại trang <a href=\"/bang-gia/\">bảng giá</a>.</p>"),
        ("Chăm sóc sau khi trồng răng Implant",
         check_list(["Tuân thủ hướng dẫn của bác sĩ về ăn uống, thuốc và vệ sinh trong những ngày đầu sau cấy.",
                     "Vệ sinh răng miệng kỹ, bao gồm vùng quanh trụ implant, để tránh viêm nướu quanh implant.",
                     "Tái khám đúng hẹn và kiểm tra định kỳ để theo dõi tình trạng trụ và răng sứ.",
                     "Hạn chế thói quen có hại như hút thuốc lá, vì có thể ảnh hưởng đến sự ổn định của implant."])),
    ],
    after_sections=None,
    steps=[("Khám &amp; chụp phim", "Bác sĩ đánh giá răng, nướu và xương hàm qua thăm khám và phim chụp. Miễn phí khi đến khám trực tiếp."),
           ("Lập kế hoạch điều trị", "Thống nhất phương án, xử lý bệnh lý răng miệng nếu có, báo giá cụ thể."),
           ("Đặt trụ implant", "Thực hiện tiểu phẫu đặt trụ vào xương hàm dưới gây tê; thời gian chờ tích hợp xương khác nhau tùy từng trường hợp."),
           ("Gắn răng sứ &amp; tái khám", "Phục hình răng sứ lên trụ và tái khám định kỳ để theo dõi lâu dài.")],
    steps_title="Quy trình trồng răng Implant",
    tail="",
    faqs=[
        ("Trồng răng Implant có đau không?", "Trong lúc thực hiện, bạn được gây tê tại chỗ nên thường không đau. Sau đó có thể ê hoặc sưng nhẹ vài ngày; bác sĩ sẽ hướng dẫn chăm sóc và dùng thuốc phù hợp nếu cần."),
        ("Trồng răng Implant mất bao lâu?", "Thời gian phụ thuộc vào từng trường hợp, đặc biệt là thời gian chờ trụ tích hợp với xương hàm và việc có cần ghép xương hay không. Bác sĩ sẽ ước tính lộ trình cụ thể sau khi thăm khám."),
        ("Ai không nên trồng răng Implant?", "Những trường hợp xương hàm không đủ điều kiện, nướu đang viêm chưa điều trị, hoặc có bệnh lý toàn thân chưa kiểm soát có thể cần xử lý trước hoặc chọn phương án khác. Hãy thông báo đầy đủ tiền sử sức khỏe để bác sĩ tư vấn chính xác."),
        ("Chi phí trồng răng Implant tại Nha khoa AVA là bao nhiêu?", "Chi phí được báo cụ thể sau khi bác sĩ thăm khám và chụp phim, vì phụ thuộc số răng, loại trụ, răng sứ phục hình và các thủ thuật đi kèm (nếu có)."),
        ("Tôi có thể được tư vấn trồng răng Implant qua điện thoại không?", "AVA không tư vấn qua điện thoại hoặc trực tuyến. Bạn vui lòng đến trực tiếp phòng khám tại Quận 10 để được bác sĩ thăm khám, chụp phim kiểm tra miễn phí và tư vấn."),
    ],
    related=["rang-su", "tram-rang-tham-my", "nieng-rang"],
)

CONTENT["rang-su"] = dict(
    title="Bọc Răng Sứ Quận 10, TPHCM | Răng Sứ Thẩm Mỹ – Nha Khoa AVA",
    desc="Bọc răng sứ quận 10 tại Nha khoa AVA: tư vấn răng sứ, mặt dán sứ để cải thiện màu sắc, hình dáng răng. Khám & chụp phim miễn phí. 283/91 Cách Mạng Tháng 8, Q.10.",
    kicker="Răng sứ thẩm mỹ",
    h1="Răng sứ quận 10, TPHCM – bọc răng sứ &amp; phục hình thẩm mỹ",
    sub="Cải thiện màu sắc, hình dáng và chức năng ăn nhai của răng với răng sứ và mặt dán sứ. Bác sĩ khám, chụp phim và tư vấn phương án ít xâm lấn phù hợp.",
    lead="Bọc răng sứ là phương pháp phục hình trong đó bác sĩ mài một lớp mô răng thật rồi gắn mão sứ lên trên để cải thiện hình dạng, màu sắc và chức năng ăn nhai của răng. Tại Nha khoa AVA, bạn được thăm khám và chụp phim kiểm tra miễn phí để bác sĩ tư vấn có nên bọc sứ hay chọn phương án ít xâm lấn hơn.",
    sections=[
        ("Khi nào nên bọc răng sứ?",
         "<p>Răng sứ thường được chỉ định trong các trường hợp:</p>"
         + check_list(["Răng sứt mẻ, vỡ lớn hoặc đã trám nhiều lần, không còn đủ mô răng để trám.",
                       "Răng ố vàng, nhiễm màu nặng mà tẩy trắng không cải thiện được.",
                       "Răng đã điều trị tủy cần được bảo vệ để tránh nứt vỡ.",
                       "Răng có hình dạng, kích thước bất thường hoặc lệch nhẹ ở vùng thẩm mỹ.",
                       "Phục hồi răng mất bằng cầu răng sứ khi không chọn implant."])),
        ("Các lựa chọn răng sứ phổ biến",
         '<div class="price-table-wrap"><table class="price-table"><thead><tr><th>Loại</th><th>Đặc điểm chung</th></tr></thead><tbody>'
         "<tr><td>Răng sứ có sườn kim loại</td><td>Sườn kim loại phủ sứ bên ngoài; chi phí thường thấp hơn, độ trong suốt của răng kém hơn loại toàn sứ.</td></tr>"
         "<tr><td>Răng toàn sứ</td><td>Không có sườn kim loại, màu sắc tự nhiên và hòa hợp với mô nướu hơn; được dùng nhiều ở vùng răng cửa.</td></tr>"
         "<tr><td>Mặt dán sứ (veneer)</td><td>Lớp sứ mỏng dán ở mặt ngoài răng, thường chỉ cần mài rất ít mô răng; phù hợp khi răng còn khỏe và cần chỉnh màu, hình dáng.</td></tr>"
         "</tbody></table></div><p class=\"price-note\">Loại sứ cụ thể, màu sắc và hình dáng răng được bác sĩ tư vấn dựa trên tình trạng từng răng và mong muốn của bạn.</p>"),
        ("Lưu ý trước khi quyết định bọc răng sứ",
         "<p>Bọc răng sứ cần mài một phần mô răng thật và thao tác này không thể hoàn tác. Vì vậy, nếu tình trạng của bạn có thể cải thiện bằng cách ít xâm lấn hơn, như <a href=\"/tram-rang-tham-my/\">trám răng thẩm mỹ</a>, tẩy trắng hoặc <a href=\"/nieng-rang/\">niềng răng</a>, bác sĩ sẽ tư vấn các phương án đó trước. Bạn nên hỏi rõ về loại vật liệu, quy trình, chi phí và chính sách bảo hành trước khi bắt đầu.</p>"),
        ("Chi phí răng sứ",
         "<p>Chi phí tính theo từng răng, tùy loại sứ và số lượng răng thực hiện. Phòng khám báo giá cụ thể sau khi thăm khám. Xem thêm tại <a href=\"/bang-gia/\">bảng giá</a>.</p>"),
    ],
    after_sections=None,
    steps=[("Khám &amp; chụp phim", "Bác sĩ kiểm tra răng, nướu và khớp cắn; chụp phim khi cần để có đánh giá đầy đủ."),
           ("Tư vấn &amp; chọn loại sứ", "Thống nhất loại sứ, màu sắc, hình dáng răng và chi phí dự kiến."),
           ("Mài răng &amp; lấy dấu", "Chuẩn bị răng, lấy dấu để chế tác răng sứ; thường có răng tạm trong thời gian chờ."),
           ("Gắn răng sứ &amp; tái khám", "Kiểm tra khớp cắn, gắn răng sứ chính thức và hẹn tái khám.")],
    steps_title="Quy trình bọc răng sứ",
    tail="",
    faqs=[
        ("Bọc răng sứ có đau không?", "Thao tác mài răng thường được thực hiện dưới gây tê nên bạn ít cảm thấy đau. Sau đó răng có thể hơi ê trong vài ngày; nếu kéo dài, hãy tái khám để bác sĩ kiểm tra."),
        ("Răng sứ dùng được bao lâu?", "Tuổi thọ phụ thuộc vào loại sứ, khớp cắn, thói quen ăn nhai và việc vệ sinh, tái khám định kỳ. Hãy hỏi rõ thời gian và chính sách bảo hành cụ thể khi tư vấn tại phòng khám."),
        ("Nên bọc răng sứ hay niềng răng?", "Hai phương pháp giải quyết vấn đề khác nhau: niềng răng di chuyển răng về đúng vị trí và giữ nguyên mô răng thật, còn bọc sứ thay đổi hình dạng, màu sắc răng nhưng phải mài răng. Bác sĩ sẽ tư vấn dựa trên tình trạng của bạn."),
        ("Chi phí làm răng sứ tại Nha khoa AVA là bao nhiêu?", "Giá tính theo từng răng và loại sứ, được báo cụ thể sau khi bác sĩ thăm khám."),
    ],
    related=["tram-rang-tham-my", "trong-rang-implant", "nieng-rang"],
)

CONTENT["tram-rang-tham-my"] = dict(
    title="Trám Răng Thẩm Mỹ Quận 10, TPHCM | Nha Khoa AVA",
    desc="Trám răng thẩm mỹ quận 10 tại Nha khoa AVA: phục hồi răng sâu, mẻ bằng vật liệu cùng màu răng, ít xâm lấn. Khám & chụp phim miễn phí tại Quận 10.",
    kicker="Trám răng thẩm mỹ",
    h1="Trám răng thẩm mỹ quận 10, TPHCM – phục hồi răng sâu, mẻ",
    sub="Dùng vật liệu cùng màu răng để phục hồi răng sâu, mẻ hoặc tạo hình lại răng, ít xâm lấn và thường hoàn tất trong một buổi hẹn.",
    lead="Trám răng thẩm mỹ là kỹ thuật dùng vật liệu composite (nhựa) cùng màu răng để lấp đầy phần răng bị sâu, mẻ hoặc tạo hình lại răng, thường thực hiện trong một buổi hẹn và giữ lại tối đa mô răng thật so với bọc sứ. Tại Nha khoa AVA, bác sĩ khám và chụp phim kiểm tra miễn phí để xác định răng nào cần trám và trám như thế nào.",
    sections=[
        ("Khi nào nên trám răng thẩm mỹ?",
         check_list(["Răng sâu ở giai đoạn sớm đến vừa, chưa tổn thương sâu vào tủy.",
                     "Răng mẻ góc, sứt nhỏ do va chạm hoặc cắn vật cứng.",
                     "Mòn cổ răng gây ê buốt hoặc mất thẩm mỹ.",
                     "Kẽ răng thưa nhỏ hoặc răng có hình dạng chưa đều, cần tạo hình lại."])
         + "<p>Với tổn thương lớn, răng đã yếu nhiều hoặc đã điều trị tủy, bác sĩ có thể tư vấn <a href=\"/rang-su/\">bọc răng sứ</a> để bảo vệ răng tốt hơn.</p>"),
        ("Ưu điểm và hạn chế",
         '<div class="price-table-wrap"><table class="price-table"><thead><tr><th>Ưu điểm</th><th>Hạn chế cần biết</th></tr></thead><tbody>'
         "<tr><td>Giữ lại tối đa mô răng thật, ít xâm lấn.</td><td>Vật liệu có thể mòn, ngả màu hoặc bong theo thời gian, đặc biệt khi ăn nhai lực mạnh hoặc vệ sinh chưa tốt.</td></tr>"
         "<tr><td>Màu sắc gần với răng thật, thẩm mỹ.</td><td>Không phù hợp với tổn thương quá lớn; khi đó cần phương án phục hình khác.</td></tr>"
         "<tr><td>Thường hoàn tất trong một buổi hẹn.</td><td>Cần tái khám định kỳ để kiểm tra miếng trám và phát hiện sâu răng tái phát.</td></tr>"
         "</tbody></table></div>"),
        ("Chăm sóc sau khi trám răng",
         check_list(["Sau khi trám, môi và lưỡi có thể còn tê; tránh nhai cho đến khi hết tê để không cắn vào má, môi.",
                     "Chải răng đúng cách, dùng chỉ nha khoa hoặc tăm nước để làm sạch kẽ răng.",
                     "Hạn chế cắn vật cứng bằng răng đã trám, như xương, đá lạnh.",
                     "Đi lấy cao răng và khám răng định kỳ để kiểm tra các miếng trám."])),
        ("Chi phí trám răng thẩm mỹ",
         "<p>Chi phí phụ thuộc vào vị trí, kích thước tổn thương và số răng cần trám. Phòng khám báo giá cụ thể sau khi thăm khám. Xem thêm tại <a href=\"/bang-gia/\">bảng giá</a>.</p>"),
    ],
    after_sections=None,
    steps=[("Khám &amp; chụp phim", "Phát hiện sâu răng, kể cả sâu ở kẽ răng, và đánh giá mức độ tổn thương."),
           ("Làm sạch &amp; loại bỏ mô sâu", "Lấy sạch phần răng sâu, tổn thương dưới gây tê khi cần."),
           ("Chọn màu &amp; trám", "Chọn màu phù hợp, trám từng lớp composite và chiếu đèn làm cứng vật liệu."),
           ("Chỉnh khớp cắn &amp; đánh bóng", "Kiểm tra khớp cắn, tạo hình và đánh bóng để răng tự nhiên, ăn nhai thoải mái.")],
    steps_title="Quy trình trám răng thẩm mỹ",
    tail="",
    faqs=[
        ("Trám răng thẩm mỹ có đau không?", "Với sâu răng nông thường ít đau. Khi cần, bác sĩ gây tê tại chỗ để bạn thoải mái trong lúc thực hiện."),
        ("Trám răng mất bao lâu?", "Thường hoàn tất trong một buổi hẹn. Thời gian cụ thể tùy số răng và mức độ tổn thương."),
        ("Miếng trám dùng được bao lâu?", "Tuổi thọ miếng trám phụ thuộc vị trí răng, kích thước miếng trám, thói quen ăn nhai và việc vệ sinh. Tái khám định kỳ giúp phát hiện sớm khi miếng trám cần sửa hoặc thay."),
        ("Trám răng hay bọc răng sứ?", "Trám giữ lại nhiều mô răng và ít xâm lấn nên thường được cân nhắc trước khi tổn thương còn nhỏ đến vừa. Khi răng tổn thương lớn hoặc yếu, bác sĩ có thể tư vấn bọc răng sứ."),
    ],
    related=["rang-su", "nieng-rang", "trong-rang-implant"],
)

HOME_FAQS = [
    ("Nha khoa quận 10 nào có niềng răng, trồng răng Implant, răng sứ và trám răng?",
     f"Nha khoa AVA tại {ADDRESS_SHORT} cung cấp các dịch vụ: <a href=\"/nieng-rang/\">niềng răng</a>, <a href=\"/trong-rang-implant/\">trồng răng Implant</a>, <a href=\"/rang-su/\">răng sứ</a> và <a href=\"/tram-rang-tham-my/\">trám răng thẩm mỹ</a>."),
    ("Nha khoa AVA mở cửa lúc mấy giờ?", "Phòng khám làm việc từ Thứ 2 đến Thứ 7, 8:00 – 17:00; nghỉ Chủ nhật."),
    ("Khám và chụp phim tại Nha khoa AVA có mất phí không?", "Khi đến trực tiếp phòng khám, bạn được bác sĩ tư vấn và chụp phim kiểm tra miễn phí. AVA không hỗ trợ tư vấn qua điện thoại hoặc trực tuyến."),
    ("Chi phí các dịch vụ nha khoa tại AVA là bao nhiêu?", "Chi phí phụ thuộc tình trạng răng và phương pháp được chọn. Bác sĩ báo giá cụ thể sau khi thăm khám và chụp phim. Bảng giá tham khảo xem tại <a href=\"/bang-gia/\">trang Bảng giá</a>."),
    ("Bác sĩ nào trực tiếp điều trị tại Nha khoa AVA?", "BS. Phạm Việt Hùng, bác sĩ Chuyên khoa Răng Hàm Mặt, chuyên chỉnh nha (niềng răng), trực tiếp thăm khám và theo dõi các ca niềng răng. Xem <a href=\"/bac-si-pham-viet-hung/\">hồ sơ bác sĩ</a>."),
    ("Làm sao để đặt lịch khám?", f"Bạn có thể gọi hotline <a href=\"tel:{PHONE_TEL}\">{PHONE}</a> hoặc nhắn Zalo 038 888 8272 để đặt lịch hẹn, sau đó đến phòng khám để được thăm khám và tư vấn trực tiếp."),
]


# ---------------------------------------------------------------------------
# BẢNG GIÁ NIỀNG RĂNG (số liệu từ website cũ)
# ---------------------------------------------------------------------------
PRICE_NIENG_ROWS = [
    ("Khám và tư vấn", "Miễn phí"),
    ("Chỉnh hình răng trẻ em (giai đoạn 1: 8–12 tuổi, giai đoạn 2: 12–14 tuổi)", "20.000.000 – 40.000.000 Vnđ"),
    ("Niềng răng mắc cài kim loại Victory – SmartClip 3M (Mỹ)", "Cấp độ 1: 20 – 40 triệu<br>Cấp độ 2: 40 – 50 triệu<br>Cấp độ 3: 50 – 60 triệu"),
    ("Niềng răng mắc cài sứ thẩm mỹ", "Cấp độ 1: 40 – 50 triệu<br>Cấp độ 2: 50 – 60 triệu<br>Cấp độ 3: 60 – 70 triệu"),
    ("Niềng răng trong suốt Invisalign", "Cấp độ 1: 60 – 80 triệu<br>Cấp độ 2: 80 – 100 triệu<br>Cấp độ 3: 100 – 120 triệu"),
    ("Mini-screw (vít neo chỉnh nha)", "2.000.000 Vnđ / cái"),
    ("Khí cụ duy trì chỉnh nha khay trong", "1.000.000 Vnđ / 1 hàm"),
    ("Khí cụ duy trì chỉnh nha Hawley", "2.000.000 Vnđ / 1 hàm"),
]
PRICE_NOTE = (f"* Cấp độ do bác sĩ đánh giá sau khi thăm khám trực tiếp. Bảng giá mang tính chất tham khảo và có thể thay đổi theo từng thời điểm "
              f"hoặc chương trình ưu đãi. Liên hệ hotline {PHONE} hoặc Zalo 038 888 8272 để được báo giá chính xác.")


def price_table(caption, rows, head=("Hạng mục", "Giá tham khảo")):
    body = "".join(f'<tr><td>{a}</td><td class="price">{b}</td></tr>' for a, b in rows)
    return (f'<div class="price-table-wrap"><table class="price-table"><caption>{caption}</caption>'
            f"<thead><tr><th>{head[0]}</th><th>{head[1]}</th></tr></thead><tbody>{body}</tbody></table></div>")


def price_nieng_methods():
    return ('<h2>Các phương pháp niềng răng tại AVA</h2>'
            '<div class="price-table-wrap"><table class="price-table"><thead><tr><th>Phương pháp</th><th>Đặc điểm</th><th>Giá tham khảo</th></tr></thead><tbody>'
            '<tr><td>Mắc cài kim loại Victory – SmartClip 3M (Mỹ)</td><td>Chi phí thấp nhất trong ba phương pháp; bác sĩ đánh giá mức độ phù hợp theo từng ca.</td><td class="price">Từ 20 triệu (cấp độ 1)</td></tr>'
            '<tr><td>Mắc cài sứ thẩm mỹ</td><td>Mắc cài có màu gần với răng, kín đáo hơn mắc cài kim loại.</td><td class="price">Từ 40 triệu (cấp độ 1)</td></tr>'
            '<tr><td>Invisalign (khay trong suốt)</td><td>Khay tháo lắp được, thẩm mỹ; cần đeo đủ thời gian theo chỉ định và không phù hợp với mọi ca.</td><td class="price">Từ 60 triệu (cấp độ 1)</td></tr>'
            '</tbody></table></div>'
            '<p class="price-note">* Cấp độ ca do bác sĩ đánh giá sau khi thăm khám. Xem đầy đủ tại <a href="/bang-gia/" style="color:var(--brand-dark);font-weight:600">bảng giá</a>.</p>')


# ---------------------------------------------------------------------------
# CÁC KHỐI DÙNG LẠI
# ---------------------------------------------------------------------------
def service_cards(keys=None, title_suffix=" quận 10"):
    out = ""
    for s in SERVICES:
        if keys and s["key"] not in keys:
            continue
        out += (f'<a class="service-card" href="{s["url"]}"><span class="sc-icon"><i class="fa-solid {s["icon"]}"></i></span>'
                f'<h3>{s["name"]}{title_suffix}</h3><p>{esc(s["short"])}</p><span class="sc-link">Xem chi tiết <i class="fa-solid fa-arrow-right"></i></span></a>')
    return f'<div class="service-grid">{out}</div>'


def gallery_tabs(active=None):
    tabs = '<a href="/hinh-anh-truoc-sau/"' + (' class="active"' if active is None else "") + ">Tất cả</a>"
    for s in SERVICES:
        tabs += f'<a href="{s["gallery_url"]}"' + (' class="active"' if active == s["key"] else "") + f'>{s["name"]}</a>'
    return f'<div class="gallery-tabs">{tabs}</div>'


def img_dims(rel):
    try:
        from PIL import Image
        with Image.open(ROOT / rel.lstrip("/")) as im:
            return f' width="{im.size[0]}" height="{im.size[1]}"'
    except Exception:
        return ""


def read_partial(name):
    return (ROOT / "partials" / name).read_text(encoding="utf-8")


def related_block(keys):
    return f"""
<section class="section">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Dịch vụ khác</span><h2>Các dịch vụ khác tại Nha khoa AVA quận 10</h2></div>
    {service_cards(keys)}
  </div>
</section>
"""


def preview_gallery(cases, svc, n=6, title="Hình ảnh trước và sau điều trị", note=""):
    if not cases:
        return ""
    items = "".join(gallery_item(c, svc, i, eager=False) for i, c in enumerate(cases[:n]))
    return f"""
<section class="section" id="hinh-anh">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Ca lâm sàng thực tế</span><h2>{title}</h2>
    <p>Một số ca đã hoàn thành tại Nha khoa AVA. Nhấn vào ảnh để xem chi tiết.{note}</p></div>
    <div class="gallery-grid">{items}</div>
    <p class="gallery-more"><a href="{svc['gallery_url']}" class="btn btn-primary"><i class="fa-solid fa-images"></i> Xem thêm ảnh {svc['name'].lower()}</a></p>
  </div>
</section>
"""


# ---------------------------------------------------------------------------
# TRANG DỊCH VỤ
# ---------------------------------------------------------------------------
def build_service_page(svc, cases):
    c = CONTENT[svc["key"]]
    trail = [("Trang chủ", "/"), (svc["name"], svc["url"])]
    lds = [dentist_ld(), website_ld(), breadcrumb_ld(trail), faq_ld(c["faqs"]),
           {"@context": "https://schema.org", "@type": "MedicalWebPage", "name": c["title"], "url": SITE + svc["url"],
            "description": c["desc"], "inLanguage": "vi-VN", "about": {"@type": "MedicalProcedure", "name": svc["name"]},
            "provider": {"@id": f"{SITE}/#dentist"}}]
    og = "/assets/images/logo/og-logo.png"
    out = head(c["title"], c["desc"], svc["url"], lds, og_image=og) + header()
    out += page_hero(trail, c["kicker"], c["h1"], c["sub"])
    body = f'<p class="answer-first">{c["lead"]}</p>'
    out += f'<section class="section"><div class="container"><div class="about-body" style="max-width:860px">{body}</div>'
    if cases:
        cs = cases[0]
        src = f'<source srcset="{cs["thumb_webp"]}" type="image/webp">' if cs["thumb_webp"] else ""
        out += (f'<div class="about-media" style="max-width:860px;margin:26px auto"><picture>{src}<img src="{cs["full"]}" '
                f'alt="{esc(svc["alts"][0].format(n=f"{cs["n"]:02d}"))}" width="900" height="1250" loading="lazy" '
                f'style="max-height:520px;width:auto;margin:0 auto;display:block;border-radius:var(--radius-md)"></picture></div>')
    out += '<div class="about-body" style="max-width:860px;margin-top:30px">'
    for h, p in c["sections"]:
        out += f"<h2>{h}</h2>{p}"
        if h.startswith("Những trường hợp") and c.get("after_sections") == "PRICE_NIENG":
            out += price_nieng_methods()
    out += "</div></div></section>"
    out += process_block(c["steps"], c["steps_title"])
    if c["tail"]:
        out += f'<section class="section"><div class="container"><div class="about-body" style="max-width:860px">{c["tail"]}</div></div></section>'
    out += preview_gallery(cases, svc, title=f"Hình ảnh {svc['name'].lower()} trước và sau")
    if svc["key"] == "nieng-rang":
        out += ('<section class="section section-alt"><div class="container"><div class="about-body" style="max-width:860px">'
                '<h2>Bác sĩ trực tiếp điều trị</h2><p>Các ca niềng răng tại AVA do BS. Phạm Việt Hùng, bác sĩ Chuyên khoa Răng Hàm Mặt, trực tiếp thăm khám, lên kế hoạch và theo dõi. '
                '<a href="/bac-si-pham-viet-hung/" style="color:var(--brand-dark);font-weight:600">Xem hồ sơ bác sĩ &rarr;</a></p></div></div></section>')
    out += faq_block(c["faqs"], f"Giải đáp thắc mắc về {svc['name'].lower()} quận 10")
    out += related_block(c["related"])
    out += cta_banner()
    out += footer()
    write(svc["url"].strip("/") + ".html", out)


# ---------------------------------------------------------------------------
# TRANG CHỦ
# ---------------------------------------------------------------------------
def build_home(all_cases):
    title = "Nha Khoa Quận 10 TPHCM | Niềng Răng, Implant, Răng Sứ – Nha Khoa AVA"
    desc = "Nha khoa quận 10 – Nha khoa AVA: niềng răng, trồng răng Implant, răng sứ, trám răng thẩm mỹ. Khám & chụp phim miễn phí, bác sĩ chuyên khoa trực tiếp điều trị."
    lds = [dentist_ld(), website_ld(), faq_ld(HOME_FAQS)]
    o = head(title, desc, "/", lds, og_image="/assets/images/logo/og-logo.png") + header()
    hero_img = "/assets/images/co-so-vat-chat/co-so-01-mat-tien-phong-kham"
    o += f"""
<section class="hero">
  <div class="container">
    <div class="hero-copy">
      <div class="hero-eyebrow-row"><span class="pill-badge">Quận 10 · TP. Hồ Chí Minh</span><span class="pill-badge">Khám &amp; chụp phim miễn phí</span></div>
      <h1>Nha khoa quận 10 – Niềng răng, trồng răng <span class="accent">Implant</span>, răng sứ, trám răng thẩm mỹ</h1>
      <p class="hero-sub">Nha khoa AVA tại Quận 10, TPHCM cung cấp các dịch vụ niềng răng, trồng răng Implant, răng sứ và trám răng thẩm mỹ. Bác sĩ chuyên khoa trực tiếp thăm khám, chụp phim kiểm tra và tư vấn phương án phù hợp với tình trạng răng của bạn.</p>
      <div class="hero-cta-row">
        <a href="#lien-he" class="btn btn-primary"><i class="fa-solid fa-calendar-check"></i> Đặt lịch khám &amp; tư vấn</a>
        <a href="tel:{PHONE_TEL}" class="btn btn-outline"><i class="fa-solid fa-phone"></i> Gọi Hotline</a>
      </div>
      <div class="hero-stats">
        <div class="stat"><b>0đ</b><span>Khám &amp; chụp phim kiểm tra tại phòng khám</span></div>
        <div class="stat"><b>4</b><span>Dịch vụ: niềng răng, Implant, răng sứ, trám răng</span></div>
        <div class="stat"><b>Q.10</b><span>283/91 Cách Mạng Tháng 8</span></div>
        <div class="stat"><b>T2–T7</b><span>Làm việc 8:00 – 17:00</span></div>
      </div>
    </div>
    <div class="hero-media">
      <div class="hero-media-frame has-img">
        <picture><source srcset="{hero_img}.webp" type="image/webp"><img src="{hero_img}.jpg" alt="Mặt tiền Nha khoa AVA – nha khoa quận 10 TPHCM" width="700" height="1088" loading="eager" fetchpriority="high"></picture>
      </div>
      <div class="hero-floating-card"><i class="fa-solid fa-user-doctor"></i><div><b>Bác sĩ trực tiếp điều trị</b><span>Khám, chụp phim, tư vấn tại phòng khám</span></div></div>
    </div>
  </div>
</section>

<section class="section section-alt" id="dich-vu">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Dịch vụ tại Nha khoa AVA</span>
      <h2>Dịch vụ nha khoa quận 10 tại AVA</h2>
      <p>Bốn nhóm dịch vụ chính, từ chỉnh nha đến phục hình và điều trị răng thẩm mỹ. Phương án cụ thể do bác sĩ tư vấn sau khi thăm khám.</p></div>
    {service_cards()}
  </div>
</section>

<section class="section" id="loi-ich">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Vì sao chọn AVA</span>
      <h2>Vì sao chọn nha khoa AVA tại quận 10</h2>
      <p>Thăm khám kỹ, tư vấn rõ ràng và theo dõi lâu dài là điều chúng tôi đặt lên hàng đầu.</p></div>
    <div class="benefit-grid">
      <div class="benefit-card"><span class="num">01</span><h3>Bác sĩ trực tiếp thăm khám</h3><p>Chẩn đoán và phác đồ điều trị do bác sĩ chuyên khoa thực hiện trực tiếp.</p></div>
      <div class="benefit-card"><span class="num">02</span><h3>Khám &amp; chụp phim miễn phí</h3><p>Được thăm khám, chụp phim kiểm tra để bác sĩ đánh giá tình trạng trước khi tư vấn phương án.</p></div>
      <div class="benefit-card"><span class="num">03</span><h3>Đa dạng dịch vụ tại một địa chỉ</h3><p>Niềng răng, Implant, răng sứ, trám răng thẩm mỹ, giúp kế hoạch điều trị liền mạch.</p></div>
      <div class="benefit-card"><span class="num">04</span><h3>Báo giá rõ ràng</h3><p>Chi phí được báo cụ thể sau khi thăm khám; bảng giá tham khảo công khai trên website.</p></div>
      <div class="benefit-card"><span class="num">05</span><h3>Kế hoạch cá nhân hóa</h3><p>Lộ trình, thời gian và chi phí được xây dựng riêng cho từng người.</p></div>
      <div class="benefit-card"><span class="num">06</span><h3>Tái khám định kỳ</h3><p>Theo dõi sau điều trị để giữ kết quả lâu dài và phát hiện sớm vấn đề phát sinh.</p></div>
    </div>
  </div>
</section>
"""
    # Quy trình
    o += process_block([("Đặt lịch hẹn", f"Gọi hotline {PHONE} hoặc nhắn Zalo để đặt lịch, sau đó đến trực tiếp phòng khám."),
                        ("Khám &amp; chụp phim", "Bác sĩ thăm khám, chụp phim kiểm tra tình trạng răng, nướu và xương hàm. Miễn phí."),
                        ("Tư vấn &amp; báo giá", "Thống nhất phương án điều trị, thời gian dự kiến và chi phí cụ thể."),
                        ("Điều trị &amp; tái khám", "Thực hiện điều trị và tái khám định kỳ để theo dõi, duy trì kết quả.")],
                       "Quy trình thăm khám tại Nha khoa AVA", kicker="Quy trình")
    # Hình ảnh cơ sở vật chất
    fac = [("co-so-02-sanh-tiep-don", "Sảnh tiếp đón Nha khoa AVA quận 10", "Sảnh tiếp đón"),
           ("co-so-03-phong-dieu-tri-nhieu-ghe", "Phòng điều trị nhiều ghế tại Nha khoa AVA quận 10", "Phòng điều trị"),
           ("co-so-04-ghe-dieu-tri-nha-khoa", "Ghế điều trị nha khoa tại Nha khoa AVA quận 10", "Ghế điều trị"),
           ("co-so-05-phong-chup-phim-ct-conebeam", "Phòng chụp phim CT Conebeam tại Nha khoa AVA quận 10", "Phòng chụp phim"),
           ("co-so-06-khu-tiet-trung-dung-cu", "Khu tiệt trùng dụng cụ tại Nha khoa AVA quận 10", "Khu tiệt trùng"),
           ("co-so-08-ekip-dieu-tri", "Ekip điều trị tại Nha khoa AVA quận 10", "Ekip điều trị")]
    fi = ""
    for stem, alt, tag in fac:
        p = f"/assets/images/co-so-vat-chat/{stem}"
        fi += (f'<div class="gallery-item" data-full="{p}.webp"><div class="thumb-frame"><picture><source srcset="{p}.webp" type="image/webp">'
               f'<img src="{p}.jpg" alt="{esc(alt)}" loading="lazy"{img_dims(p + ".webp")}></picture></div><span class="tag">{tag}</span></div>')
    o += f"""
<section class="section" id="co-so">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Cơ sở vật chất</span>
      <h2>Không gian nha khoa AVA tại Quận 10</h2><p>Phòng khám tại 283/91 Cách Mạng Tháng 8, Quận 10. Nhấn vào ảnh để xem chi tiết.</p></div>
    <div class="gallery-grid facility-grid">{fi}</div>
  </div>
</section>
"""
    # Hình ảnh ca thực tế: lấy luân phiên giữa các dịch vụ đã có ảnh
    non_empty = [s for s in SERVICES if all_cases[s["key"]]]
    items, tot = "", 0
    if non_empty:
        per = max(2, -(-6 // len(non_empty)))
        for s in non_empty:
            for i, c in enumerate(all_cases[s["key"]][:per]):
                items += gallery_item(c, s, i, tag=f"{s['name']} · Ca {c['n']:02d}")
                tot += 1
    o += f"""
<section class="section section-alt" id="hinh-anh">
  <div class="container">
    <div class="section-head center"><span class="kicker"><span class="dot"></span>Ca lâm sàng thực tế</span>
      <h2>Hình ảnh trước và sau điều trị tại Nha khoa AVA</h2><p>Chọn dịch vụ để xem các ca đã hoàn thành. Nhấn vào ảnh để xem chi tiết.</p></div>
    {gallery_tabs()}
    <div class="gallery-grid">{items}</div>
    <p class="gallery-more"><a href="/hinh-anh-truoc-sau/" class="btn btn-primary"><i class="fa-solid fa-images"></i> Xem tất cả hình ảnh</a></p>
  </div>
</section>
"""
    # Bảng giá tóm tắt
    o += f"""
<section class="section">
  <div class="container">
    <div class="section-head"><span class="kicker"><span class="dot"></span>Bảng giá</span><h2>Bảng giá tham khảo tại nha khoa AVA quận 10</h2>
      <p>Chi phí thực tế phụ thuộc tình trạng răng và phương pháp chọn; bác sĩ báo giá cụ thể sau khi thăm khám và chụp phim.</p></div>
    <div class="price-tables-grid"><div class="price-table-wrap"><table class="price-table"><caption>Giá tham khảo</caption>
      <thead><tr><th>Dịch vụ</th><th>Giá tham khảo</th></tr></thead><tbody>
      <tr><td>Khám và tư vấn</td><td class="price">Miễn phí</td></tr>
      <tr><td><a href="/nieng-rang/">Niềng răng mắc cài kim loại</a></td><td class="price">Từ 20 triệu (cấp độ 1)</td></tr>
      <tr><td><a href="/nieng-rang/">Niềng răng mắc cài sứ</a></td><td class="price">Từ 40 triệu (cấp độ 1)</td></tr>
      <tr><td><a href="/nieng-rang/">Niềng răng Invisalign</a></td><td class="price">Từ 60 triệu (cấp độ 1)</td></tr>
      <tr><td><a href="/trong-rang-implant/">Trồng răng Implant</a></td><td class="price">{price_fmt(PRICE_OTHER[0][2])}</td></tr>
      <tr><td><a href="/rang-su/">Răng sứ</a></td><td class="price">{price_fmt(PRICE_OTHER[2][2])}</td></tr>
      <tr><td><a href="/tram-rang-tham-my/">Trám răng thẩm mỹ</a></td><td class="price">{price_fmt(PRICE_OTHER[4][2])}</td></tr>
      </tbody></table></div></div>
    <p class="price-note">{PRICE_NOTE} <a href="/bang-gia/" style="color:var(--brand-dark);font-weight:600">Xem trang Bảng giá &rarr;</a></p>
  </div>
</section>
"""
    o += read_partial("doctor.html").replace('<section class="section">', '<section class="section section-alt">', 1)
    o += faq_block(HOME_FAQS, "Giải đáp thắc mắc về nha khoa quận 10 tại AVA", alt=False)
    o += cta_banner("Sẵn sàng chăm sóc nụ cười của bạn?")
    con = read_partial("contact.html")
    con = con.replace("Đặt lịch tư vấn niềng răng trả góp", "Đặt lịch khám tại nha khoa AVA quận 10")
    o += con
    o += footer()
    write("index.html", o)


# ---------------------------------------------------------------------------
# BẢNG GIÁ
# ---------------------------------------------------------------------------
def build_prices():
    trail = [("Trang chủ", "/"), ("Bảng giá", "/bang-gia/")]
    title = "Bảng Giá Nha Khoa Quận 10 | Niềng Răng, Implant, Răng Sứ – Nha Khoa AVA"
    desc = "Bảng giá tham khảo niềng răng, trồng răng Implant, răng sứ, trám răng thẩm mỹ tại Nha khoa AVA quận 10. Báo giá cụ thể sau khi thăm khám và chụp phim miễn phí."
    o = head(title, desc, "/bang-gia/", [dentist_ld(), breadcrumb_ld(trail)]) + header()
    o += page_hero(trail, "Bảng giá", "Bảng giá nha khoa quận 10 tại Nha khoa AVA",
                   "Giá tham khảo các dịch vụ niềng răng, trồng răng Implant, răng sứ và trám răng thẩm mỹ. Chi phí chính xác được báo sau khi bác sĩ thăm khám.")
    other = [(f"<strong>{a}</strong><br><span style='font-size:13px;color:var(--ink-faint)'>{b}</span>", price_fmt(c)) for a, b, c in PRICE_OTHER]
    o += f"""
<section class="section">
  <div class="container">
    <div class="price-tables-grid">
      {price_table('Niềng răng (chỉnh nha)', PRICE_NIENG_ROWS)}
      {price_table('Trồng răng Implant, răng sứ, trám răng', other)}
    </div>
    <p class="price-note">{PRICE_NOTE}</p>
    <div class="about-body" style="max-width:860px;margin-top:28px">
      <h2>Vì sao chi phí được báo sau khi thăm khám?</h2>
      <p>Mỗi người có tình trạng răng, xương hàm và mong muốn khác nhau. Chi phí niềng răng phụ thuộc cấp độ ca; chi phí Implant phụ thuộc số lượng răng, loại trụ và thủ thuật đi kèm; chi phí răng sứ và trám răng tính theo từng răng. Vì vậy bác sĩ cần thăm khám và chụp phim trước khi báo giá. Việc này hoàn toàn miễn phí khi bạn đến trực tiếp phòng khám.</p>
      <p>Tìm hiểu chi tiết từng dịch vụ: {" · ".join(f'<a href="{s["url"]}">{s["name"]}</a>' for s in SERVICES)}.</p>
    </div>
  </div>
</section>
"""
    o += cta_banner() + footer()
    write("bang-gia.html", o)


# ---------------------------------------------------------------------------
# THƯ VIỆN ẢNH
# ---------------------------------------------------------------------------
def build_gallery_pages(all_cases):
    # từng dịch vụ
    for s in SERVICES:
        cases = all_cases[s["key"]]
        trail = [("Trang chủ", "/"), ("Hình ảnh", "/hinh-anh-truoc-sau/"), (s["name"], s["gallery_url"])]
        title = f"Hình Ảnh {s['name'].title()} Trước Và Sau Quận 10 | Nha Khoa AVA"
        desc = f"Hình ảnh {s['name'].lower()} trước và sau tại Nha khoa AVA quận 10, TPHCM. Các ca thực tế đã hoàn thành, bác sĩ chuyên khoa trực tiếp điều trị."
        robots = "index, follow" if cases else "noindex, follow"
        o = head(title, desc, s["gallery_url"], [breadcrumb_ld(trail)], robots=robots) + header()
        o += page_hero(trail, "Ca lâm sàng thực tế", f"Hình ảnh {s['name'].lower()} trước và sau tại nha khoa quận 10",
                       f"Các ca {s['name'].lower()} đã hoàn thành tại Nha khoa AVA. Kết quả mỗi người khác nhau tùy tình trạng ban đầu; bác sĩ tư vấn cụ thể sau khi thăm khám.", ctas=False)
        o += '<section class="section"><div class="container">' + gallery_tabs(s["key"])
        if cases:
            items = ""
            for i, c in enumerate(cases):
                items += gallery_item(c, s, i, eager=i < 4, hidden=i >= 24)
            o += f'<div class="gallery-grid">{items}</div>'
            if len(cases) > 24:
                o += (f'<p class="gallery-more"><button type="button" class="btn btn-primary" id="gallery-load-more"><i class="fa-solid fa-plus"></i> '
                      f'Xem thêm ảnh (<span id="gallery-left">{len(cases) - 24}</span>)</button></p>')
        else:
            o += (f'<div class="case-empty"><i class="fa-regular fa-images"></i><h2>Đang cập nhật hình ảnh ca {s["name"].lower()}</h2>'
                  f'<p>Các ca thực tế sẽ sớm được đăng tải. Trong thời gian này, bạn có thể tìm hiểu thêm về <a href="{s["url"]}">{s["name"].lower()} quận 10</a> '
                  f'hoặc đặt lịch để được bác sĩ thăm khám trực tiếp.</p></div>')
        o += f'<p class="gallery-more"><a href="{s["url"]}" class="btn btn-outline">Tìm hiểu về {s["name"].lower()} quận 10</a></p></div></section>'
        o += cta_banner() + footer()
        write(s["gallery_file"], o)
    # trang tổng
    trail = [("Trang chủ", "/"), ("Hình ảnh", "/hinh-anh-truoc-sau/")]
    title = "Hình Ảnh Trước Và Sau Điều Trị | Nha Khoa Quận 10 – Nha Khoa AVA"
    desc = "Hình ảnh trước và sau điều trị niềng răng, trồng răng Implant, răng sứ, trám răng thẩm mỹ tại Nha khoa AVA quận 10, TPHCM."
    o = head(title, desc, "/hinh-anh-truoc-sau/", [breadcrumb_ld(trail)]) + header()
    o += page_hero(trail, "Ca lâm sàng thực tế", "Hình ảnh trước và sau điều trị tại nha khoa quận 10 AVA",
                   "Các ca thực tế đã hoàn thành, chia theo từng dịch vụ. Nhấn vào ảnh để xem chi tiết.", ctas=False)
    o += '<section class="section"><div class="container">' + gallery_tabs(None)
    for s in SERVICES:
        cases = all_cases[s["key"]]
        o += f'<div class="section-head" style="margin-top:34px"><h2 style="font-size:clamp(22px,2.6vw,30px)">{s["name"]} quận 10</h2></div>'
        if cases:
            o += '<div class="gallery-grid">' + "".join(gallery_item(c, s, i) for i, c in enumerate(cases[:6])) + "</div>"
            o += f'<p class="gallery-more"><a href="{s["gallery_url"]}" class="btn btn-primary"><i class="fa-solid fa-images"></i> Xem tất cả ca {s["name"].lower()} ({len(cases)} ca)</a></p>'
        else:
            o += f'<div class="case-empty"><i class="fa-regular fa-images"></i><p>Đang cập nhật hình ảnh ca {s["name"].lower()}.</p></div>'
    o += "</div></section>" + cta_banner() + footer()
    write("hinh-anh-truoc-sau.html", o)


# ---------------------------------------------------------------------------
# TRANG NỘI DUNG CŨ (giới thiệu, bác sĩ, bài kiến thức) - giữ nội dung, thay khung
# ---------------------------------------------------------------------------
LINK_MAP = {
    "/bang-gia-nieng-rang-tra-gop/": "/bang-gia/",
    "/hinh-anh-nieng-rang-truoc-sau/": "/hinh-anh-nieng-rang/",
}
OVERRIDES = {
    "gioi-thieu.html": dict(
        title="Giới Thiệu Nha Khoa AVA – Nha Khoa Quận 10 TPHCM",
        desc="Giới thiệu Nha khoa AVA – nha khoa quận 10, TPHCM: niềng răng, trồng răng Implant, răng sứ, trám răng thẩm mỹ. 283/91 Cách Mạng Tháng 8, Quận 10."),
}


TEXT_PATCH = {
    "gioi-thieu.html": [
        ("Các dịch vụ tại AVA gồm chỉnh hình răng hàm mặt (niềng răng), phục hình răng sứ thẩm mỹ, tẩy trắng răng và điều trị các bệnh lý răng miệng.",
         "Các dịch vụ tại AVA gồm chỉnh hình răng hàm mặt (niềng răng), trồng răng Implant, phục hình răng sứ thẩm mỹ, trám răng thẩm mỹ, tẩy trắng răng và điều trị các bệnh lý răng miệng."),
    ],
}


def build_content_pages():
    for f in sorted((ROOT / "content").glob("*.html")):
        t = f.read_text(encoding="utf-8")
        t = t.replace("https://niengrangtphcm.vn", SITE).replace("niengrangtphcm.vn", "nhakhoaavadental.vn")
        for a, b in LINK_MAP.items():
            t = t.replace(a, b)
        t = re.sub(r'<header class="site-header">.*?</header>\n?', lambda m: header(), t, flags=re.S)
        t = re.sub(r'<footer class="site-footer">.*</html>\s*$', lambda m: footer().lstrip("\n"), t, flags=re.S)
        t = re.sub(r"\?v=\d+[a-z]?", f"?v={ASSET_V}", t)
        for a, b in TEXT_PATCH.get(f.name, []):
            if a not in t:
                print("  ! không tìm thấy đoạn cần thay trong", f.name)
            t = t.replace(a, b)
        ov = OVERRIDES.get(f.name)
        if ov:
            t = re.sub(r"<title>.*?</title>", lambda m: f"<title>{esc(ov['title'])}</title>", t, flags=re.S)
            t = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(ov["desc"]) + m.group(2), t)
            t = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + esc(ov["title"]) + m.group(2), t)
            t = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + esc(ov["desc"]) + m.group(2), t)
            t = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")', lambda m: m.group(1) + esc(ov["title"]) + m.group(2), t)
            t = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', lambda m: m.group(1) + esc(ov["desc"]) + m.group(2), t)
        write(f.name, t)


# ---------------------------------------------------------------------------
# SITEMAP / ROBOTS
# ---------------------------------------------------------------------------
def build_sitemap(all_cases):
    urls = ["/", "/nieng-rang/", "/trong-rang-implant/", "/rang-su/", "/tram-rang-tham-my/", "/bang-gia/", "/hinh-anh-truoc-sau/"]
    urls += [s["gallery_url"] for s in SERVICES if all_cases[s["key"]]]
    urls += ["/gioi-thieu/", "/bac-si-pham-viet-hung/", "/nieng-rang-tra-gop-dieu-kien-thu-tuc/",
             "/nieng-rang-mac-cai-hay-invisalign/", "/nieng-rang-bao-lau-co-dau-khong/"]
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    x += "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    x += "</urlset>\n"
    write("sitemap.xml", x)
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")


def main():
    print("1) Xử lý ảnh mới...")
    for s in SERVICES:
        process_folder(s)
    all_cases = {s["key"]: collect_cases(s) for s in SERVICES}
    for s in SERVICES:
        print(f"   {s['name']}: {len(all_cases[s['key']])} ca")
    print("2) Sinh trang...")
    build_home(all_cases)
    for s in SERVICES:
        build_service_page(s, all_cases[s["key"]])
    build_prices()
    build_gallery_pages(all_cases)
    build_content_pages()
    build_sitemap(all_cases)
    print("Xong.")


if __name__ == "__main__":
    main()
