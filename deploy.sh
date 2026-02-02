#!/usr/bin/env bash
set -euo pipefail

# -------- CONFIG --------
MAIN_BRANCH="main"
PAGES_BRANCH="gh-pages"
APK_BASENAME="game.apk"
TITLE_TEXT="Tiny Wings"
TMP_DIR="/tmp/tw_webdeploy"
BUILD_DIR="build/web"

# -------- HELPERS --------
die() { echo "❌ $*" >&2; exit 1; }
info() { echo "✅ $*"; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Commande manquante: $1"; }

# -------- PRECHECKS --------
require_cmd git
require_cmd python

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Pas dans un repo git"

CUR_BRANCH="$(git branch --show-current)"
[ "$CUR_BRANCH" = "$MAIN_BRANCH" ] || die "Tu dois être sur '$MAIN_BRANCH' (actuel: $CUR_BRANCH)"

# Working tree clean
git diff --quiet || die "Working tree non clean (commit/stash avant)."
git diff --cached --quiet || die "Index non clean (git status)."

# -------- BUILD (pygbag) --------
info "Build web via pygbag..."
python -m pip install -q --upgrade pip
python -m pip install -q pygbag

rm -rf build
python -m pygbag .

[ -d "$BUILD_DIR" ] || die "Build folder introuvable: $BUILD_DIR"
[ -f "$BUILD_DIR/index.html" ] || die "index.html introuvable dans $BUILD_DIR"

# -------- RENAME APK + PATCH HTML --------
info "Renommage APK + patch index.html..."
APK_SRC="$(ls "$BUILD_DIR"/*.apk 2>/dev/null | head -n 1 || true)"
[ -n "$APK_SRC" ] || die "Aucun .apk trouvé dans $BUILD_DIR"

mv "$APK_SRC" "$BUILD_DIR/$APK_BASENAME"

# remplace le nom de l'apk dans index.html
perl -pi -e "s/\"[^\"]+\.apk\"/\"$APK_BASENAME\"/g" "$BUILD_DIR/index.html"
perl -pi -e "s/Loading [^ ]+/Loading $TITLE_TEXT/g" "$BUILD_DIR/index.html"

# -------- PREP DEPLOY DIR --------
info "Préparation du dossier temporaire..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cp -R "$BUILD_DIR/." "$TMP_DIR/"

# Pages needs .nojekyll
touch "$TMP_DIR/.nojekyll"
find "$TMP_DIR" -name ".DS_Store" -delete

# -------- DEPLOY TO GH-PAGES --------
info "Déploiement sur $PAGES_BRANCH..."
git checkout "$PAGES_BRANCH" >/dev/null 2>&1 || die "Branche $PAGES_BRANCH introuvable (créée-la une fois)."

git rm -rf . >/dev/null 2>&1 || true
cp -R "$TMP_DIR/." .
git add -A
git commit -m "Deploy web build" || info "Rien à commit (identique)."
git push -f origin "$PAGES_BRANCH"

# back to main
git checkout "$MAIN_BRANCH" >/dev/null 2>&1

info "Déploiement terminé ✅"