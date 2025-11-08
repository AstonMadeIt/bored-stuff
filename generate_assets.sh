#!/usr/bin/env bash
# Top-tier image export pipeline for macOS (ImageMagick + cwebp + avifenc)
# Source files expected in this folder:
#   hero-stars-source.jpg
#   grit-red-source.jpg
#   newspaper-source.jpg

set -euo pipefail

# ---------- pretty logging ----------
b() { printf "\033[1m%s\033[0m\n" "$*"; }
ok() { printf "✅ %s\n" "$*"; }
warn() { printf "⚠️  %s\n" "$*"; }
err() { printf "❌ %s\n" "$*" >&2; }

# ---------- dependency checks ----------
need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing '$1'. Install with Homebrew: brew install $2"
    exit 1
  fi
}
need magick imagemagick
need cwebp webp
need avifenc libavif

# ---------- structure ----------
OUT="_exports"
SNIPS="_snippets"
mkdir -p "$OUT/hero" "$OUT/grit" "$OUT/news" "$SNIPS"

# ---------- helpers ----------
jpg()   { magick "$1" -strip -quality "${3:-88}" "$2"; }
webp()  { cwebp -q "${3:-82}" "$1" -o "$2" >/dev/null 2>&1; }
avif()  { avifenc --min "${3:-28}" --max "${4:-36}" --speed "${5:-6}" --jobs 8 "$1" "$2" >/dev/null 2>&1; }

# =====================================================================
# A) HERO — 21:9 crop → JPG/WebP/AVIF at multiple widths + LQIP
# =====================================================================
if [[ -f "hero-stars-source.jpg" ]]; then
  b "A) HERO 21:9"
  SRC="hero-stars-source.jpg"
  TMP="$OUT/hero/_hero-6000-temp.jpg"

  # Create large working canvas (keeps crop math clean)
  magick "$SRC" -resize 6000x -gravity center -crop 21:9 +repage "$TMP"
  ok "Prepared temp: $TMP"

  for W in 3840 2560 1920 1280 768; do
    BASE="$OUT/hero/hero-stars-${W}"
    # JPG
    magick "$TMP" -resize "${W}x" -strip -quality 88 "${BASE}.jpg"
    # WebP
    webp "${BASE}.jpg" "${BASE}.webp" 82
    # AVIF
    avif "${BASE}.jpg" "${BASE}.avif" 28 36 6
    ok "Rendered hero size ${W}px → JPG/WebP/AVIF"
  done

  # LQIP blur-up (tiny, blurred placeholder)
  magick "$TMP" -resize 40x -blur 0x8 -quality 40 "$OUT/hero/hero-stars-blur.jpg"
  ok "LQIP: $OUT/hero/hero-stars-blur.jpg"

  # snippet
  cat > "$SNIPS/hero-picture.html" <<'HTML'
<!-- HERO: paste into your HTML -->
<picture>
  <source type="image/avif"
          srcset="/_exports/hero/hero-stars-3840.avif 3840w,
                  /_exports/hero/hero-stars-2560.avif 2560w,
                  /_exports/hero/hero-stars-1920.avif 1920w,
                  /_exports/hero/hero-stars-1280.avif 1280w,
                  /_exports/hero/hero-stars-768.avif 768w"
          sizes="(min-width:1280px) 90vw, 100vw">
  <source type="image/webp"
          srcset="/_exports/hero/hero-stars-3840.webp 3840w,
                  /_exports/hero/hero-stars-2560.webp 2560w,
                  /_exports/hero/hero-stars-1920.webp 1920w,
                  /_exports/hero/hero-stars-1280.webp 1280w,
                  /_exports/hero/hero-stars-768.webp 768w"
          sizes="(min-width:1280px) 90vw, 100vw">
  <img src="/_exports/hero/hero-stars-1280.jpg"
       srcset="/_exports/hero/hero-stars-3840.jpg 3840w,
               /_exports/hero/hero-stars-2560.jpg 2560w,
               /_exports/hero/hero-stars-1920.jpg 1920w,
               /_exports/hero/hero-stars-1280.jpg 1280w,
               /_exports/hero/hero-stars-768.jpg 768w"
       sizes="(min-width:1280px) 90vw, 100vw"
       alt="Starfield hero"
       style="background:url('/_exports/hero/hero-stars-blur.jpg') center/cover no-repeat; display:block; width:100%; aspect-ratio:21/9;">
</picture>
HTML
  ok "Snippet: $SNIPS/hero-picture.html"
else
  warn "Skipped HERO (hero-stars-source.jpg not found)."
fi

# =====================================================================
# B) GRIT RED TILE — square crop, deband, contrast pop, optional seam
# =====================================================================
if [[ -f "grit-red-source.jpg" ]]; then
  b "B) GRIT RED TILE"
  SRC="grit-red-source.jpg"
  BASE="$OUT/grit/grit-red-2048"
  WORK="$OUT/grit/grit-red-2048-work.jpg"

  # Square crop to 2048, light blur to remove banding, contrast pop
  magick "$SRC" -resize 2048x2048^ -gravity center -crop 2048x2048+0+0 \
         -sigmoidal-contrast 4x30% -blur 0x0.2 "$WORK"

  # Quick & dirty seamless trick (rolled average)
  magick "$WORK" \( -clone 0 -roll +1024+1024 \) -average "${BASE}-seamless.jpg"

  # Formats
  cp "${BASE}-seamless.jpg" "${BASE}.jpg"
  webp "${BASE}-seamless.jpg" "$OUT/grit/grit-red.webp" 80
  avif "${BASE}-seamless.jpg" "$OUT/grit/grit-red.avif" 28 34 6
  ok "Rendered GRIT → ${BASE}.jpg / grit-red.webp / grit-red.avif"

  # snippet
  cat > "$SNIPS/grit-css.html" <<'HTML'
<!-- GRIT TILE as CSS background -->
<style>
.bg-grit {
  background-image: image-set(
    url("/_exports/grit/grit-red.avif") type("image/avif"),
    url("/_exports/grit/grit-red.webp") type("image/webp"),
    url("/_exports/grit/grit-red-2048.jpg") type("image/jpeg")
  );
  background-size: 512px 512px; /* tweak tile size */
  background-repeat: repeat;
}
</style>
<!-- Usage: <div class="bg-grit">...</div> -->
HTML
  ok "Snippet: $SNIPS/grit-css.html"
else
  warn "Skipped GRIT (grit-red-source.jpg not found)."
fi

# =====================================================================
# C) NEWSPAPER TEXTURE — square crop, grayscale, normalize
# =====================================================================
if [[ -f "newspaper-source.jpg" ]]; then
  b "C) NEWSPAPER TEXTURE"
  SRC="newspaper-source.jpg"
  BASE="$OUT/news/newspaper-53"

  magick "$SRC" -resize 2048x2048^ -gravity center -crop 2048x2048+0+0 \
         -colorspace Gray -contrast-stretch 0.5%x0.5% -normalize \
         "${BASE}.jpg"

  webp "${BASE}.jpg" "${BASE}.webp" 75
  avif "${BASE}.jpg" "${BASE}.avif" 30 38 6
  ok "Rendered NEWSPAPER → ${BASE}.jpg/.webp/.avif"

  # snippet
  cat > "$SNIPS/newspaper-css.html" <<'HTML'
<!-- Subtle paper texture overlay -->
<style>
.texture-paper {
  position: relative;
}
.texture-paper::after {
  content: "";
  position: absolute; inset: 0;
  pointer-events: none; mix-blend-mode: multiply; opacity: .25;
  background-image: image-set(
    url("/_exports/news/newspaper-53.avif") type("image/avif"),
    url("/_exports/news/newspaper-53.webp") type("image/webp"),
    url("/_exports/news/newspaper-53.jpg") type("image/jpeg")
  );
  background-size: cover;
}
</style>
<!-- Usage: <section class="texture-paper">...</section> -->
HTML
  ok "Snippet: $SNIPS/newspaper-css.html"
else
  warn "Skipped NEWSPAPER (newspaper-source.jpg not found)."
fi

b "Done."
ok "Exports in: $OUT"
ok "Snippets in: $SNIPS"
