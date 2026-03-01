/**
 * gallery-loader.js
 * Dynamically loads photos for any gallery on a public portfolio page.
 *
 * Usage: place <div class="gallery-grid" data-gallery="portfolio-maternity">
 *        on any page, and include this script. It will fetch /api/gallery/<id>
 *        and render the images automatically.
 *
 * PUBLIC API: No authentication required (read-only).
 */

(function () {
    const SVG_ZOOM = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="none"
    stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
  </svg>`;

    async function loadGallery(container) {
        const galleryId = container.dataset.gallery;
        if (!galleryId) return;
        try {
            const res = await fetch(`/api/gallery/${galleryId}`);
            const data = await res.json();
            if (!data.images || !data.images.length) {
                container.innerHTML = '<p style="text-align:center;padding:40px;color:#8c7b70">Gallery coming soon.</p>';
                return;
            }
            container.innerHTML = data.images.map((img, i) => `
        <div class="gallery-item fade-in${i % 3 === 1 ? ' fade-in-delay-1' : i % 3 === 2 ? ' fade-in-delay-2' : ''}"
             data-src="images/${img.filename}">
          <img src="images/${img.filename}" alt="${img.alt || 'Portfolio photo'}" loading="lazy" />
          <div class="gallery-overlay">${SVG_ZOOM}</div>
        </div>`).join('');

            // Re-init lightbox if main.js exposes it
            if (typeof window.initLightbox === 'function') window.initLightbox();
        } catch (e) {
            container.innerHTML = '<p style="text-align:center;padding:40px;color:#8c7b70">Gallery unavailable.</p>';
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.gallery-grid[data-gallery]').forEach(loadGallery);
    });
})();
