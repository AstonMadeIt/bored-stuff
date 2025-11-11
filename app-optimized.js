// ===========================
// FAANG-GRADE TIKTOK EMBED OPTIMIZATION
// L7+ Implementation with CEO-Proof Features
// ===========================

(function () {
  'use strict';

  // ===========================
  // Configuration
  // ===========================
  const CONFIG = {
    OBSERVER_ROOT_MARGIN: '50px 0px', // Tighter margin (was 120px) - just-in-time loading
    OBSERVER_THRESHOLD: 0.1,
    AUTOPLAY: true,
    MUTED: true,
    CONTROLS: 1,
    REL: 0, // Show only same author's videos as related content
    LOOP: 0, // TikTok loop is unreliable, we'll handle it ourselves
  };

  // ===========================
  // Feature Detection
  // ===========================
  const SUPPORTS_INTERSECTION_OBSERVER = 'IntersectionObserver' in window;
  const PREFERS_REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ===========================
  // TikTok Embed Handler
  // ===========================
  class TikTokEmbed {
    constructor(container) {
      this.container = container;
      this.url = container.dataset.tiktokUrl;
      this.title = container.dataset.title || 'TikTok video';
      this.posterSrc = container.dataset.poster;
      this.isLoaded = false;
      this.iframe = null;

      this.init();
    }

    init() {
      // Set up poster image
      const posterImg = this.container.querySelector('.ttk__poster-img');
      if (posterImg && this.posterSrc) {
        posterImg.src = this.posterSrc;
      }

      // Add click handler to poster button
      const posterButton = this.container.querySelector('.ttk__poster');
      if (posterButton) {
        posterButton.addEventListener('click', (e) => {
          e.preventDefault();
          this.load();
          this.trackEvent('video_play_clicked');
        });
      }
    }

    load() {
      if (this.isLoaded) return;

      // Extract video ID from URL
      const videoId = this.url.split('/').pop().split('?')[0];
      if (!videoId) {
        console.warn('Invalid TikTok URL:', this.url);
        return;
      }

      // Create iframe with all optimizations
      this.iframe = document.createElement('iframe');
      
      // Build embed URL with parameters
      const embedUrl = new URL(`https://www.tiktok.com/embed/v2/${videoId}`);
      embedUrl.searchParams.set('autoplay', CONFIG.AUTOPLAY ? '1' : '0');
      embedUrl.searchParams.set('muted', CONFIG.MUTED ? '1' : '0');
      embedUrl.searchParams.set('controls', CONFIG.CONTROLS);
      embedUrl.searchParams.set('rel', CONFIG.REL);
      embedUrl.searchParams.set('loop', CONFIG.LOOP);
      
      this.iframe.src = embedUrl.toString();

      // Accessibility
      this.iframe.title = this.title;
      
      // Security: Sandbox the iframe
      this.iframe.sandbox = 'allow-scripts allow-same-origin allow-presentation';
      
      // Referrer policy for privacy
      this.iframe.referrerPolicy = 'no-referrer-when-downgrade';
      
      // Legacy scroll prevention attribute (belt & suspenders)
      this.iframe.setAttribute('scrolling', 'no');
      
      // Allow fullscreen
      this.iframe.allow = 'fullscreen';
      this.iframe.allowFullscreen = true;

      // Error handling
      this.iframe.addEventListener('error', () => {
        console.warn('TikTok embed failed to load:', videoId);
        this.handleLoadError();
        this.trackEvent('video_load_error', { videoId });
      }, { once: true });

      // Success tracking
      this.iframe.addEventListener('load', () => {
        this.trackEvent('video_loaded', { videoId });
      }, { once: true });

      // Create frame wrapper with aspect ratio
      const frameWrapper = document.createElement('div');
      frameWrapper.className = 'ttk__frame';
      frameWrapper.appendChild(this.iframe);

      // Replace poster with iframe
      this.container.innerHTML = '';
      this.container.appendChild(frameWrapper);

      this.isLoaded = true;
    }

    unload() {
      if (!this.isLoaded) return;

      // Remove iframe to free resources
      if (this.iframe) {
        this.iframe.src = '';
        this.iframe = null;
      }

      // Restore poster
      this.container.innerHTML = `
        <button class="ttk__poster" type="button" aria-label="Play TikTok video: ${this.title}">
          <img class="ttk__poster-img" src="${this.posterSrc}" alt="TikTok video preview: ${this.title}" loading="lazy" decoding="async">
          <span class="ttk__play" aria-hidden="true">▶</span>
        </button>
      `;

      // Re-initialize
      this.isLoaded = false;
      this.init();
    }

    handleLoadError() {
      // Fallback UI on error
      const fallbackLink = this.container.closest('.press-card').querySelector('.press-link');
      if (fallbackLink) {
        fallbackLink.style.display = 'block';
      }
      
      // Optional: Show error message
      const errorMsg = document.createElement('div');
      errorMsg.className = 'ttk__error';
      errorMsg.innerHTML = `
        <p>Video unavailable</p>
        <a href="${this.url}" target="_blank" rel="noopener">Watch on TikTok →</a>
      `;
      this.container.innerHTML = '';
      this.container.appendChild(errorMsg);
    }

    trackEvent(eventName, data = {}) {
      // Analytics instrumentation
      // Integrate with your analytics provider (GA4, Segment, etc.)
      if (typeof gtag !== 'undefined') {
        gtag('event', eventName, {
          event_category: 'TikTok Embed',
          ...data
        });
      }
      
      // Or custom logging
      if (window.analyticsQueue) {
        window.analyticsQueue.push({
          event: eventName,
          timestamp: Date.now(),
          ...data
        });
      }

      // Console logging for development
      if (window.location.hostname === 'localhost') {
        console.log('[Analytics]', eventName, data);
      }
    }
  }

  // ===========================
  // Intersection Observer Setup
  // ===========================
  function setupLazyLoading() {
    const containers = document.querySelectorAll('.ttk');
    if (!containers.length) return;

    // Skip auto-loading if user prefers reduced motion
    if (PREFERS_REDUCED_MOTION) {
      console.log('Reduced motion preference detected, skipping auto-load');
      containers.forEach(container => {
        new TikTokEmbed(container);
      });
      return;
    }

    if (SUPPORTS_INTERSECTION_OBSERVER) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const embed = entry.target.__tiktokEmbed;
          
          if (entry.isIntersecting) {
            // Load when entering viewport
            if (!embed.isLoaded) {
              embed.load();
            }
          } else {
            // Optional: Unload when leaving viewport to free resources
            // This creates a "loop-like" effect when scrolling back
            if (embed.isLoaded) {
              // Uncomment to enable viewport-based unloading
              // embed.unload();
            }
          }
        });
      }, {
        rootMargin: CONFIG.OBSERVER_ROOT_MARGIN,
        threshold: CONFIG.OBSERVER_THRESHOLD
      });

      containers.forEach(container => {
        const embed = new TikTokEmbed(container);
        container.__tiktokEmbed = embed;
        observer.observe(container);
      });
    } else {
      // Fallback for browsers without IntersectionObserver
      containers.forEach(container => {
        const embed = new TikTokEmbed(container);
        // Load immediately as fallback
        setTimeout(() => embed.load(), 1000);
      });
    }
  }

  // ===========================
  // Performance Monitoring
  // ===========================
  function monitorPerformance() {
    if (!window.performance || !window.performance.getEntriesByType) return;

    // Monitor FPS during scroll
    let frameCount = 0;
    let lastTime = performance.now();
    
    function checkFPS() {
      const now = performance.now();
      const delta = now - lastTime;
      
      if (delta >= 1000) {
        const fps = Math.round((frameCount * 1000) / delta);
        if (fps < 55) {
          console.warn(`Low FPS detected: ${fps}fps`);
        }
        frameCount = 0;
        lastTime = now;
      }
      
      frameCount++;
      requestAnimationFrame(checkFPS);
    }

    // Only monitor in development
    if (window.location.hostname === 'localhost') {
      requestAnimationFrame(checkFPS);
    }

    // Log performance metrics
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfData = performance.getEntriesByType('navigation')[0];
        if (perfData) {
          console.log('Performance Metrics:', {
            'DNS Lookup': `${Math.round(perfData.domainLookupEnd - perfData.domainLookupStart)}ms`,
            'TCP Connection': `${Math.round(perfData.connectEnd - perfData.connectStart)}ms`,
            'DOM Interactive': `${Math.round(perfData.domInteractive)}ms`,
            'DOM Complete': `${Math.round(perfData.domComplete)}ms`,
            'Page Load': `${Math.round(perfData.loadEventEnd - perfData.fetchStart)}ms`
          });
        }
      }, 0);
    });
  }

  // ===========================
  // Initialize Everything
  // ===========================
  function init() {
    // Wait for DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }

    // Set up TikTok embeds
    setupLazyLoading();

    // Monitor performance in development
    if (window.location.hostname === 'localhost') {
      monitorPerformance();
    }

    // Handle browser back/forward navigation
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) {
        // Page was restored from cache
        setupLazyLoading();
      }
    });
  }

  // Start the app
  init();

  // Export for testing/debugging
  window.TikTokEmbed = TikTokEmbed;

})();

// ===========================
// Additional App Functionality
// (Charts, animations, etc. from original app.js)
// ===========================

// ... rest of your original app.js code for charts, Three.js, etc. goes here ...
