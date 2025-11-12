// ===== DEPENDENCY CHECKER =====
// Ensures all libraries loaded before init
class DependencyManager {
  constructor() {
    this.required = ['Plotly', 'gsap', 'THREE', 'Tone'];
    this.checkInterval = null;
  }

  async waitForDependencies() {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Libraries failed to load within 10s'));
      }, 10000);

      this.checkInterval = setInterval(() => {
        const allLoaded = this.required.every(lib => window[lib] !== undefined);
        if (allLoaded) {
          clearInterval(this.checkInterval);
          clearTimeout(timeout);
          resolve();
        }
      }, 100);
    });
  }
}

// ===== THEME MANAGER =====
class ThemeManager {
  constructor() {
    this.currentTheme = localStorage.getItem('theme') || 'light';
    this.toggleButton = null;
  }

  init() {
    this.applyTheme(this.currentTheme);
    this.createToggle();
  }

  createToggle() {
    const headerControls = document.querySelector('.header-controls');
    if (!headerControls) return;

    const toggle = document.createElement('button');
    toggle.className = 'theme-toggle';
    toggle.setAttribute('aria-label', 'Toggle dark mode');
    toggle.innerHTML = `
      <span class="theme-toggle-icon">🌙</span>
      <span class="theme-toggle-text">Dark</span>
    `;
    
    // Insert before music toggle
    const musicToggle = document.getElementById('music-toggle');
    if (musicToggle) {
      headerControls.insertBefore(toggle, musicToggle);
    } else {
      headerControls.appendChild(toggle);
    }

    toggle.addEventListener('click', () => this.toggle());
    this.toggleButton = toggle;
    this.updateToggleButton();
  }

  toggle() {
    this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.applyTheme(this.currentTheme);
    localStorage.setItem('theme', this.currentTheme);
    this.updateToggleButton();
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  updateToggleButton() {
    if (!this.toggleButton) return;
    const icon = this.toggleButton.querySelector('.theme-toggle-icon');
    const text = this.toggleButton.querySelector('.theme-toggle-text');
    
    if (this.currentTheme === 'dark') {
      icon.textContent = '☀️';
      text.textContent = 'Light';
    } else {
      icon.textContent = '🌙';
      text.textContent = 'Dark';
    }
  }
}

// ===== LOADER MANAGER =====
class LoaderManager {
  constructor() {
    this.loader = document.getElementById('loader');
    this.progress = document.querySelector('.loader-progress');
    this.currentProgress = 0;
    this.interval = null;
  }

  start() {
    this.interval = setInterval(() => {
      this.currentProgress += Math.random() * 30;
      if (this.currentProgress >= 100) {
        this.complete();
      } else {
        this.progress.style.width = `${this.currentProgress}%`;
      }
    }, 200);
  }

  complete() {
    clearInterval(this.interval);
    this.currentProgress = 100;
    this.progress.style.width = '100%';
    setTimeout(() => {
      this.loader.classList.add('hidden');
    }, 500);
  }
}

// ===== AUDIO ENGINE =====
class AudioEngine {
  constructor() {
    this.audioStarted = false;
    this.musicEnabled = false;
    this.synths = {};
    this.loops = {};
    this.effects = {};
  }

  init() {
    try {
      this.effects.reverb = new Tone.Reverb({ 
        decay: 12, preDelay: 0.02, wet: 0.8 
      }).toDestination();
      
      this.effects.delay = new Tone.FeedbackDelay("8n.", 0.6)
        .connect(this.effects.reverb);

      this.synths.bells = new Tone.Synth({ 
        oscillator: { type: "sine" }, 
        envelope: { attack: .05, decay: 2, sustain: .3, release: 4 }, 
        volume: -32 
      }).connect(this.effects.delay);

      this.synths.subBass = new Tone.Synth({ 
        oscillator: { type: "sine" }, 
        envelope: { attack: .01, decay: .5, sustain: .7, release: 1 }, 
        volume: -12 
      }).toDestination();

      this.synths.bass808 = new Tone.MembraneSynth({ 
        pitchDecay: .1, octaves: 3, 
        oscillator: { type: "sine" }, 
        envelope: { attack: .001, decay: .4, sustain: .05, release: 1 }, 
        volume: -18 
      }).toDestination();

      this.synths.ambient = new Tone.Synth({ 
        oscillator: { type: "triangle" }, 
        envelope: { attack: 6, decay: 4, sustain: .5, release: 8 }, 
        volume: -28 
      }).connect(this.effects.reverb);

      this.setupMusicToggle();
      this.setupVolumeControl();
    } catch (e) {
      console.warn('Audio setup failed:', e);
    }
  }

  setupMusicToggle() {
    const toggle = document.getElementById('music-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', () => {
      if (!this.audioStarted) {
        Tone.start();
        this.audioStarted = true;
      }

      this.musicEnabled = !this.musicEnabled;
      toggle.setAttribute('aria-pressed', this.musicEnabled);

      const icon = toggle.querySelector('.music-toggle-icon');
      const text = toggle.querySelector('.music-toggle-text');

      if (this.musicEnabled) {
        this.startMusic();
        icon.textContent = '🔊';
        text.textContent = 'Music On';
      } else {
        this.stopMusic();
        icon.textContent = '🔇';
        text.textContent = 'Music Off';
      }
    });
  }

  setupVolumeControl() {
    const slider = document.getElementById('volume-slider');
    if (!slider) return;

    slider.addEventListener('input', (e) => {
      const volume = parseInt(e.target.value);
      const db = -60 + (volume * 0.6); // Maps 0-100 to -60db to 0db
      Tone.Destination.volume.value = db;
    });
  }

  startMusic() {
    if (this.loops.main) return;

    const progression = [
      ["C3", "E3", "G3"], 
      ["A2", "C3", "E3"], 
      ["F2", "A2", "C3"], 
      ["G2", "B2", "D3"]
    ];

    const bassProg = ["C1", "A1", "F1", "G1"];
    const bellsMelody = ["C5", "E5", "G5", "C6", "G5", "E5"];

    this.loops.main = new Tone.Loop(time => {
      const beat = Math.floor(Tone.Transport.seconds) % 4;
      const chord = progression[beat];

      chord.forEach((note, i) => {
        this.synths.ambient.triggerAttackRelease(note, "2n", time + i * 0.05);
      });

      this.synths.subBass.triggerAttackRelease(bassProg[beat], "2n", time);

      if (Math.random() > 0.7) {
        this.synths.bass808.triggerAttackRelease(bassProg[beat], "16n", time);
      }

      if (Math.random() > 0.85) {
        const noteIdx = Math.floor(Math.random() * bellsMelody.length);
        this.synths.bells.triggerAttackRelease(
          bellsMelody[noteIdx], 
          "8n", 
          time + Math.random() * 0.3
        );
      }
    }, "2n").start(0);

    Tone.Transport.bpm.value = 58;
    Tone.Transport.start();
  }

  stopMusic() {
    if (this.loops.main) {
      this.loops.main.stop();
      this.loops.main.dispose();
      this.loops.main = null;
    }
    Tone.Transport.stop();
  }

  cleanup() {
    this.stopMusic();
    Object.values(this.synths).forEach(synth => synth.dispose());
    Object.values(this.effects).forEach(effect => effect.dispose());
  }
}

// ===== THREE.JS BACKGROUND =====
class ThreeBackground {
  constructor() {
    this.canvas = document.getElementById('three-bg');
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.particles = null;
    this.animationId = null;
  }

  init() {
    if (!this.canvas || !window.THREE) return;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      75, 
      window.innerWidth / window.innerHeight, 
      0.1, 
      1000
    );
    this.camera.position.z = 50;

    this.renderer = new THREE.WebGLRenderer({ 
      canvas: this.canvas, 
      alpha: true, 
      antialias: false 
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

    this.createParticles();
    this.animate();
    this.handleResize();
  }

  createParticles() {
    const geometry = new THREE.BufferGeometry();
    const count = 800;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 100;
      positions[i + 1] = (Math.random() - 0.5) * 100;
      positions[i + 2] = (Math.random() - 0.5) * 100;

      const hue = Math.random() * 0.2 + 0.5; // Blue-purple range
      colors[i] = hue;
      colors[i + 1] = hue * 0.8;
      colors[i + 2] = 1;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
  }

  animate() {
    this.animationId = requestAnimationFrame(() => this.animate());

    if (this.particles) {
      this.particles.rotation.x += 0.0001;
      this.particles.rotation.y += 0.0002;
      
      const time = Date.now() * 0.0001;
      const positions = this.particles.geometry.attributes.position.array;
      
      for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] = Math.sin(time + i) * 2;
      }
      
      this.particles.geometry.attributes.position.needsUpdate = true;
    }

    this.renderer.render(this.scene, this.camera);
  }

  handleResize() {
    window.addEventListener('resize', () => {
      if (!this.camera || !this.renderer) return;
      
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  cleanup() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    if (this.renderer) {
      this.renderer.dispose();
    }
    if (this.particles) {
      this.particles.geometry.dispose();
      this.particles.material.dispose();
    }
  }
}

// ===== CUSTOM CURSOR =====
class CustomCursor {
  constructor() {
    this.cursor = document.getElementById('custom-cursor');
    this.mouseX = 0;
    this.mouseY = 0;
    this.cursorX = 0;
    this.cursorY = 0;
  }

  init() {
    if (!this.cursor || window.innerWidth <= 768) return;

    document.addEventListener('mousemove', (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
    });

    this.animate();

    document.querySelectorAll('a, button, .press-card').forEach(el => {
      el.addEventListener('mouseenter', () => {
        this.cursor.style.transform = 'translate(-50%, -50%) scale(2)';
      });
      el.addEventListener('mouseleave', () => {
        this.cursor.style.transform = 'translate(-50%, -50%) scale(1)';
      });
    });
  }

  animate() {
    this.cursorX += (this.mouseX - this.cursorX) * 0.1;
    this.cursorY += (this.mouseY - this.cursorY) * 0.1;

    this.cursor.style.left = `${this.cursorX}px`;
    this.cursor.style.top = `${this.cursorY}px`;

    requestAnimationFrame(() => this.animate());
  }
}

// ===== GSAP ANIMATIONS =====
class AnimationManager {
  constructor() {
    this.scrollTriggers = [];
  }

  init() {
    if (!window.gsap || !window.ScrollTrigger) return;

    gsap.registerPlugin(ScrollTrigger);

    // Set initial states
    gsap.set('.hero', { opacity: 0, y: 30 });
    gsap.set('.press, .voice-moment, .story-card, .nyt-memo-image', { 
      opacity: 0, 
      y: 50 
    });

    // Hero entrance
    gsap.to('.hero', { 
      opacity: 1, 
      y: 0, 
      duration: 1.2, 
      ease: 'power3.out', 
      delay: 0.3 
    });

    // Scroll animations
    this.createScrollAnimation('.press');
    this.createScrollAnimation('.nyt-memo-image');
    
    gsap.utils.toArray('.story-card').forEach(card => {
      this.createScrollAnimation(card);
    });

    gsap.utils.toArray('.voice-moment').forEach(moment => {
      this.createScrollAnimation(moment);
    });

    // Progress bar
    this.initProgressBar();
    
    // Header scroll state
    this.initHeaderScroll();
    
    // Back to top button
    this.initBackToTop();
  }

  createScrollAnimation(selector) {
    const trigger = gsap.to(selector, {
      scrollTrigger: { 
        trigger: selector, 
        start: 'top 85%', 
        toggleActions: 'play none none none' 
      },
      opacity: 1, 
      y: 0, 
      duration: 0.8, 
      ease: 'power2.out'
    });
    this.scrollTriggers.push(trigger);
  }

  initProgressBar() {
    const progressBar = document.querySelector('.progress-bar');
    const throttledScroll = this.throttle(() => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrollPercentage = scrollTop / scrollHeight;
      gsap.to(progressBar, { scaleX: scrollPercentage, duration: 0.1 });
    }, 16);

    window.addEventListener('scroll', throttledScroll, { passive: true });
  }

  initHeaderScroll() {
    const header = document.querySelector('header');
    const throttledScroll = this.throttle(() => {
      if (window.scrollY > 100) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }, 100);

    window.addEventListener('scroll', throttledScroll, { passive: true });
  }

  initBackToTop() {
    const button = document.querySelector('.back-to-top');
    const progressRing = document.querySelector('.progress-ring-progress');
    const radius = 24;
    const circumference = 2 * Math.PI * radius;
    
    progressRing.style.strokeDasharray = circumference;
    progressRing.style.strokeDashoffset = circumference;

    const throttledScroll = this.throttle(() => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scrollPercentage = scrollTop / scrollHeight;

      button.classList.toggle('visible', scrollTop > 500);

      const offset = circumference - (scrollPercentage * circumference);
      progressRing.style.strokeDashoffset = offset;
    }, 16);

    window.addEventListener('scroll', throttledScroll, { passive: true });

    button.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Magnetic hover effect
    if (window.innerWidth > 768) {
      button.addEventListener('mousemove', (e) => {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        gsap.to(button, { x: x * 0.3, y: y * 0.3, duration: 0.3 });
      });

      button.addEventListener('mouseleave', () => {
        gsap.to(button, { x: 0, y: 0, duration: 0.3 });
      });
    }
  }

  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  cleanup() {
    this.scrollTriggers.forEach(trigger => {
      if (trigger && trigger.kill) trigger.kill();
    });
    if (ScrollTrigger) {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    }
  }
}

// ===== CHART MANAGER =====
class ChartManager {
  constructor() {
    this.charts = {};
    this.anxietyMetrics = [
      { key: 'tradwife', name: 'Tradwife Searches', color: null },
      { key: 'measles', name: 'Measles Cases', color: null },
      { key: 'unemployment', name: 'Unemployment', color: null },
      { key: 'eggs', name: 'Egg Prices', color: null },
      { key: 'gold', name: 'Gold', color: null },
      { key: 'beef', name: 'Beef', color: null }
    ];
    this.activeMetrics = {};
  }

  init() {
    if (!window.Plotly) {
      console.error('Plotly not loaded');
      return;
    }

    this.loadColors();
    this.initIntimacyChart();
    this.initAnxietyChart();
    this.handleResize();
  }

  loadColors() {
    const css = (key) => getComputedStyle(document.documentElement)
      .getPropertyValue(key).trim();
    
    this.anxietyMetrics.forEach(metric => {
      metric.color = css(`--c-${metric.key}`);
    });
  }

  initIntimacyChart() {
    const isMobile = window.innerWidth < 480;
    const isTablet = window.innerWidth < 768;

    const data = [
      {
        hovertemplate: "%{y:.0f} times/year<extra></extra>",
        line: { color: "#FF3333", width: 4 },
        marker: { color: "#FF3333", size: 8 },
        mode: "lines+markers",
        name: "Sexual frequency",
        x: [2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2021, 2022, 2024],
        y: [66.98, 67.70, 64.02, 61.05, 63.82, 59.00, 78.18, 58.33, 55.38, 58.60, 50.13, 54.34, 49.53],
        type: "scatter",
        xaxis: "x",
        yaxis: "y"
      },
      {
        hovertemplate: "%{y:.0f}M<extra></extra>",
        line: { color: "#0066CC", dash: "dot", width: 4 },
        marker: { color: "#0066CC", size: 8, symbol: "diamond" },
        mode: "lines+markers",
        name: "SSRI prescriptions",
        x: [2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022],
        y: [164, 180, 196, 215, 232, 264, 286, 308, 330, 352, 380, 408],
        type: "scatter",
        xaxis: "x",
        yaxis: "y2"
      },
      {
        fill: "tozeroy",
        fillcolor: "rgba(0, 102, 204, 0.1)",
        hovertemplate: "%{y:.1f}%<extra></extra>",
        line: { color: "#0066CC", width: 4 },
        marker: { color: "#0066CC", size: 8 },
        mode: "lines+markers",
        name: "Marriage rate",
        showlegend: false,
        x: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022],
        y: [48.76, 48.28, 48.02, 47.86, 47.72, 47.54, 47.50, 47.80, 47.75, 47.62, 48.04, 48.02],
        type: "scatter",
        xaxis: "x2",
        yaxis: "y3"
      },
      {
        fill: "tozeroy",
        fillcolor: "rgba(102, 187, 106, 0.1)",
        hovertemplate: "%{y:.1f} hrs/day<extra></extra>",
        line: { color: "#66BB6A", width: 4 },
        marker: { color: "#66BB6A", size: 8, symbol: "square" },
        mode: "lines+markers",
        name: "Screen time",
        showlegend: false,
        x: [2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024],
        y: [8.6, 9.5, 10.3, 11.0, 11.4, 13.5, 13.8, 14.2],
        type: "scatter",
        xaxis: "x3",
        yaxis: "y4"
      }
    ];

    const layout = {
      plot_bgcolor: "rgba(0,0,0,0)",
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Space Grotesk, sans-serif", color: "#e5e5e5" },
      height: isMobile ? 500 : 480,
      margin: { l: isMobile ? 50 : 60, r: isMobile ? 20 : 60, t: 30, b: 80 },
      hovermode: "x unified",
      showlegend: true,
      legend: {
        orientation: isTablet ? "h" : "v",
        x: isTablet ? 0.5 : 1.02,
        xanchor: isTablet ? "center" : "left",
        y: isTablet ? -0.2 : 1,
        yanchor: isTablet ? "bottom" : "top",
        bgcolor: "rgba(0,0,0,0.5)",
        bordercolor: "rgba(255,255,255,0.1)",
        borderwidth: 1,
        font: { size: isMobile ? 10 : 12 }
      },
      grid: {
        rows: 2,
        columns: 2,
        pattern: "independent",
        roworder: "top to bottom",
        xgap: 0.12,
        ygap: 0.15
      },
      xaxis: {
        title: { text: "Sexual Frequency", font: { size: isMobile ? 11 : 13 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        zeroline: false,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      yaxis: {
        title: { text: "Times/year", font: { size: isMobile ? 10 : 12 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      xaxis2: {
        title: { text: "Marriage Rate", font: { size: isMobile ? 11 : 13 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      yaxis2: {
        title: { text: "Prescriptions (M)", font: { size: isMobile ? 10 : 12 } },
        gridcolor: "rgba(255,255,255,0.05)",
        side: "right",
        overlaying: "y",
        showgrid: false,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      yaxis3: {
        title: { text: "% Adults", font: { size: isMobile ? 10 : 12 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      xaxis3: {
        title: { text: "Screen Time", font: { size: isMobile ? 11 : 13 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        tickfont: { size: isMobile ? 9 : 11 }
      },
      yaxis4: {
        title: { text: "Hours/day", font: { size: isMobile ? 10 : 12 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        tickfont: { size: isMobile ? 9 : 11 }
      }
    };

    const config = {
      responsive: true,
      displayModeBar: false,
      scrollZoom: false
    };

    Plotly.newPlot("intimacy-chart", data, layout, config);
    this.charts.intimacy = document.getElementById("intimacy-chart");
  }

  initAnxietyChart() {
    const isMobile = window.innerWidth < 480;
    const isTablet = window.innerWidth < 768;

    // Initialize all metrics as active
    this.anxietyMetrics.forEach(m => {
      this.activeMetrics[m.key] = true;
    });

    const data = {
      tradwife: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [8, 12, 15, 22, 28, 35, 42, 58, 75, 100, 85, 72]
      },
      measles: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [2, 3, 5, 8, 12, 15, 22, 35, 58, 75, 100, 95]
      },
      unemployment: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [25, 95, 78, 45, 32, 28, 25, 22, 20, 25, 28, 30]
      },
      eggs: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [15, 18, 22, 28, 45, 72, 100, 68, 45, 52, 58, 62]
      },
      gold: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [55, 65, 58, 52, 58, 62, 68, 72, 85, 92, 95, 100]
      },
      beef: {
        x: ["2020-01", "2020-07", "2021-01", "2021-07", "2022-01", "2022-07", "2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
        y: [45, 52, 58, 65, 72, 78, 82, 88, 92, 95, 98, 100]
      }
    };

    this.renderAnxietyChart(data, isMobile, isTablet);
    this.createMetricToggles(data, isMobile, isTablet);
  }

  renderAnxietyChart(data, isMobile, isTablet) {
    const traces = this.anxietyMetrics
      .filter(m => this.activeMetrics[m.key])
      .map(metric => ({
        x: data[metric.key].x,
        y: data[metric.key].y,
        name: metric.name,
        type: "scatter",
        mode: "lines+markers",
        line: { color: metric.color, width: 3 },
        marker: { size: 6, color: metric.color },
        hovertemplate: `%{y}<extra>${metric.name}</extra>`
      }));

    const layout = {
      plot_bgcolor: "rgba(0,0,0,0)",
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Space Grotesk, sans-serif", color: "#e5e5e5" },
      height: isMobile ? 400 : 450,
      margin: { l: isMobile ? 40 : 60, r: isMobile ? 20 : 40, t: 30, b: 80 },
      hovermode: "x unified",
      showlegend: true,
      legend: {
        orientation: isTablet ? "h" : "v",
        x: isTablet ? 0.5 : 1.02,
        xanchor: isTablet ? "center" : "left",
        y: isTablet ? -0.25 : 1,
        yanchor: isTablet ? "bottom" : "top",
        bgcolor: "rgba(0,0,0,0.5)",
        bordercolor: "rgba(255,255,255,0.1)",
        borderwidth: 1,
        font: { size: isMobile ? 10 : 12 }
      },
      xaxis: {
        title: { text: "Timeline", font: { size: isMobile ? 11 : 13 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        zeroline: false,
        tickfont: { size: isMobile ? 9 : 11 },
        tickformat: "%b %Y"
      },
      yaxis: {
        title: { text: "Normalized Index (0-100)", font: { size: isMobile ? 10 : 12 } },
        gridcolor: "rgba(255,255,255,0.05)",
        showgrid: true,
        range: [0, 105],
        tickfont: { size: isMobile ? 9 : 11 }
      }
    };

    const config = {
      responsive: true,
      displayModeBar: false,
      scrollZoom: false
    };

    Plotly.newPlot("anxiety-chart", traces, layout, config);
    this.charts.anxiety = document.getElementById("anxiety-chart");
  }

  createMetricToggles(data, isMobile, isTablet) {
    const container = document.getElementById('anxiety-toggles');
    if (!container) return;

    container.innerHTML = '';
    
    this.anxietyMetrics.forEach(metric => {
      const button = document.createElement('button');
      button.className = 'metric-toggle active';
      button.setAttribute('data-metric', metric.key);
      button.style.setProperty('--metric-color', metric.color);
      button.innerHTML = `
        <span class="metric-toggle-indicator"></span>
        <span class="metric-toggle-name">${metric.name}</span>
      `;
      
      button.addEventListener('click', () => {
        this.activeMetrics[metric.key] = !this.activeMetrics[metric.key];
        button.classList.toggle('active');
        this.renderAnxietyChart(data, isMobile, isTablet);
      });
      
      container.appendChild(button);
    });
  }

  handleResize() {
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (this.charts.intimacy) {
          Plotly.Plots.resize(this.charts.intimacy);
        }
        if (this.charts.anxiety) {
          Plotly.Plots.resize(this.charts.anxiety);
        }
      }, 250);
    });
  }
}

// ===== TIKTOK EMBED HANDLER (NEW!) =====
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
    embedUrl.searchParams.set('autoplay', '1');
    embedUrl.searchParams.set('muted', '1');
    
    this.iframe.src = embedUrl.toString();

    // Accessibility
    this.iframe.title = this.title;
    
    // Security: Sandbox the iframe
    this.iframe.sandbox = 'allow-scripts allow-same-origin allow-presentation';
    
    // Referrer policy for privacy
    this.iframe.referrerPolicy = 'no-referrer-when-downgrade';
    
    // Legacy scroll prevention attribute
    this.iframe.setAttribute('scrolling', 'no');
    
    // Allow fullscreen
    this.iframe.allow = 'fullscreen';
    this.iframe.allowFullscreen = true;

    // Error handling
    this.iframe.addEventListener('error', () => {
      console.warn('TikTok embed failed to load:', videoId);
      this.handleLoadError();
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

  handleLoadError() {
    const errorMsg = document.createElement('div');
    errorMsg.className = 'ttk__error';
    errorMsg.innerHTML = `
      <p>Video unavailable</p>
      <a href="${this.url}" target="_blank" rel="noopener">Watch on TikTok →</a>
    `;
    this.container.innerHTML = '';
    this.container.appendChild(errorMsg);
  }
}

// ===== TIKTOK LAZY LOADING =====
function setupTikTokEmbeds() {
  const containers = document.querySelectorAll('.ttk');
  if (!containers.length) return;

  const PREFERS_REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SUPPORTS_INTERSECTION_OBSERVER = 'IntersectionObserver' in window;

  if (PREFERS_REDUCED_MOTION || !SUPPORTS_INTERSECTION_OBSERVER) {
    // Fallback: init immediately but don't auto-load
    containers.forEach(container => new TikTokEmbed(container));
    return;
  }

  // Use IntersectionObserver for lazy loading
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.__tiktokEmbed) {
        entry.target.__tiktokEmbed = new TikTokEmbed(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, {
    rootMargin: '50px 0px',
    threshold: 0.1
  });

  containers.forEach(container => observer.observe(container));
}

// ===== APP ORCHESTRATOR =====
class App {
  constructor() {
    this.depManager = new DependencyManager();
    this.themeManager = new ThemeManager();
    this.loaderManager = new LoaderManager();
    this.audioEngine = new AudioEngine();
    this.threeBackground = new ThreeBackground();
    this.customCursor = new CustomCursor();
    this.animationManager = new AnimationManager();
    this.chartManager = new ChartManager();
  }

  async init() {
    try {
      // Start loader
      this.loaderManager.start();

      // Initialize theme first (affects colors)
      this.themeManager.init();

      // Wait for dependencies
      await this.depManager.waitForDependencies();

      // Initialize all modules
      this.audioEngine.init();
      this.threeBackground.init();
      this.customCursor.init();
      this.animationManager.init();
      this.chartManager.init();
      
      // Initialize TikTok embeds
      setupTikTokEmbeds();

      // Complete loader
      this.loaderManager.complete();

    } catch (error) {
      console.error('Initialization error:', error);
      this.loaderManager.complete();
    }
  }

  cleanup() {
    this.audioEngine.cleanup();
    this.threeBackground.cleanup();
    this.animationManager.cleanup();
  }
}

// ===== ENTRY POINT =====
let app;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    app.init();
  });
} else {
  app = new App();
  app.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (app) app.cleanup();
});

// Export for debugging
window.App = App;
