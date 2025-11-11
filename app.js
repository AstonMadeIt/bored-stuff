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

  // Initialize synths/effects - ONLY called after Tone.start()
  initAudio() {
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

      Tone.getDestination().volume.value = -22;
    } catch (error) {
      console.error('Audio initialization failed:', error);
    }
  }

  async start() {
    // First click: start audio context and init everything
    if (!this.audioStarted) {
      try {
        await Tone.start();
        this.initAudio();
        this.audioStarted = true;
      } catch (error) {
        console.error('Failed to start audio context:', error);
        return;
      }
    }

    // Toggle music on/off
    if (this.musicEnabled) {
      this.stop();
      return;
    }

    // Start the music
    try {
      const bellMelody = ["E5", null, "G5", null, "A5", null, "E5", null, 
                          "D5", null, "A4", null, "E5", null, null, null, 
                          "G5", null, "A5", null, "B5", null, "A5", null, 
                          "G5", null, "E5", null, "D5", null, null, null];
      let bellIndex = 0;

      this.loops.bells = new Tone.Loop((time) => {
        const note = bellMelody[bellIndex];
        if (note) {
          this.synths.bells.triggerAttackRelease(note, "2n", time);
        }
        bellIndex = (bellIndex + 1) % bellMelody.length;
      }, "4n");

      this.loops.subBass = new Tone.Loop((time) => {
        this.synths.subBass.triggerAttackRelease("C1", "4n", time);
      }, "2n");

      this.loops.bass = new Tone.Loop((time) => {
        this.synths.bass808.triggerAttackRelease("C1", "8n", time);
        this.synths.bass808.triggerAttackRelease("C1", "16n", time + 0.375);
      }, "1n");

      this.loops.pad = new Tone.Loop((time) => {
        this.synths.ambient.triggerAttackRelease("C2", "1m", time);
      }, "1m");

      this.loops.bells.start(0);
      this.loops.subBass.start("1m");
      this.loops.bass.start("2m");
      this.loops.pad.start(0);

      Tone.getTransport().bpm.value = 140;
      Tone.getTransport().start();
      this.musicEnabled = true;
    } catch (error) {
      console.error('Failed to start soundscape:', error);
    }
  }

  stop() {
    Object.values(this.loops).forEach(loop => {
      if (loop && loop.stop) loop.stop();
    });
    if (Tone.getTransport) {
      Tone.getTransport().stop();
    }
    this.musicEnabled = false;
  }

  playClick() {
    if (this.audioStarted && this.synths.bells) {
      this.synths.bells.triggerAttackRelease("A5", "32n", "+0.02");
    }
  }

  playHover() {
    if (this.audioStarted && this.synths.bells) {
      this.synths.bells.triggerAttackRelease("E5", "64n", "+0.01");
    }
  }

  setVolume(value) {
    if (!Tone.getDestination) return;
    const volumeDb = -60 + (value / 100) * 50;
    Tone.getDestination().volume.value = volumeDb;
  }

  cleanup() {
    this.stop();
    Object.values(this.synths).forEach(synth => {
      if (synth && synth.dispose) synth.dispose();
    });
    Object.values(this.effects).forEach(effect => {
      if (effect && effect.dispose) effect.dispose();
    });
  }
}

// ===== CURSOR MANAGER =====
class CursorManager {
  constructor(audioEngine) {
    this.cursor = document.getElementById('custom-cursor');
    this.audioEngine = audioEngine;
    this.mouseX = 0;
    this.mouseY = 0;
    this.cursorX = 0;
    this.cursorY = 0;
    this.rafId = null;
  }

  init() {
    if (window.innerWidth <= 768) {
      document.body.style.cursor = 'auto';
      this.cursor.style.display = 'none';
      return;
    }

    document.addEventListener('mousemove', (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
    });

    this.animate();
    this.attachHoverListeners();
  }

  animate() {
    this.cursorX += (this.mouseX - this.cursorX) * 0.2;
    this.cursorY += (this.mouseY - this.cursorY) * 0.2;
    this.cursor.style.left = `${this.cursorX}px`;
    this.cursor.style.top = `${this.cursorY}px`;
    this.rafId = requestAnimationFrame(() => this.animate());
  }

  attachHoverListeners() {
    const elements = document.querySelectorAll('a, button, .metric-btn, .story-card');
    elements.forEach(el => {
      el.addEventListener('mouseenter', () => {
        this.cursor.classList.add('hover');
        // Only play sound if audio is actually started
        if (this.audioEngine?.audioStarted) {
          this.audioEngine.playHover();
        }
      });
      el.addEventListener('mouseleave', () => {
        this.cursor.classList.remove('hover');
      });
      el.addEventListener('click', () => {
        // Only play sound if audio is actually started
        if (this.audioEngine?.audioStarted) {
          this.audioEngine.playClick();
        }
      });
    });
  }

  cleanup() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
  }
}

// ===== THREE.JS BACKGROUND =====
class ThreeBackground {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.particles = null;
    this.mouseX = 0;
    this.mouseY = 0;
    this.frame = 0;
    this.rafId = null;
  }

  init() {
    if (window.innerWidth <= 768) return;

    try {
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(
        75, 
        window.innerWidth / window.innerHeight, 
        0.1, 
        1000
      );
      this.camera.position.z = 50;

      const canvas = document.getElementById('three-bg');
      this.renderer = new THREE.WebGLRenderer({ 
        canvas, 
        alpha: true, 
        antialias: false 
      });
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

      this.createParticles();
      this.animate();
      this.handleResize();

      document.addEventListener('mousemove', (e) => {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;
      });
    } catch (error) {
      console.error('Three.js init failed:', error);
    }
  }

  createParticles() {
    const geometry = new THREE.BufferGeometry();
    const count = 800;
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 200;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const material = new THREE.PointsMaterial({
      size: 1.0,
      color: 0xff6b9d,
      transparent: true,
      opacity: 0.15,
      blending: THREE.NormalBlending
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
  }

  animate() {
    this.rafId = requestAnimationFrame(() => this.animate());

    // Skip every other frame for performance
    if (this.frame % 2 !== 0) {
      this.frame++;
      return;
    }

    if (this.particles) {
      this.particles.rotation.y += 0.0002;
      this.particles.rotation.x += 0.0001;
      this.particles.rotation.y += this.mouseX * 0.00003;
      this.particles.rotation.x += this.mouseY * 0.00003;
    }

    this.renderer.render(this.scene, this.camera);
    this.frame++;
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
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
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

// ===== ANIMATION CONTROLLER =====
class AnimationController {
  constructor() {
    this.scrollTriggers = [];
  }

  init() {
    if (!window.gsap) {
      console.error('GSAP not loaded');
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Hero animations
    gsap.to('.hero-title', { 
      opacity: 1, y: 0, duration: 1.2, ease: 'power3.out', delay: 0.3 
    });
    gsap.to('.hero-subtitle', { 
      opacity: 1, y: 0, duration: 1, ease: 'power3.out', delay: 0.6 
    });

    // Scroll-triggered reveals
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
        fillcolor: "rgba(0,0,0,0.1)",
        hovertemplate: "%{y:.1f} hours<extra></extra>",
        line: { color: "#000", width: 4 },
        marker: { color: "#000", size: 8 },
        mode: "lines+markers",
        name: "Screen time",
        showlegend: false,
        x: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022],
        y: [2.7, 3.2, 3.8, 4.5, 5.2, 5.9, 6.8, 7.4, 8.1, 8.5, 10.2, 10.5, 10.8],
        type: "scatter",
        xaxis: "x3",
        yaxis: "y4"
      }
    ];

    const layout = {
      xaxis: {
        anchor: "y",
        domain: [0.0, 0.94],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: true,
        linewidth: 1,
        linecolor: "rgba(0,0,0,.15)",
        ticks: "outside",
        ticklen: 4,
        tickcolor: "rgba(0,0,0,.15)",
        type: "linear",
        dtick: isTablet ? 4 : 2,
        range: [1999, 2025],
        zeroline: false,
        tickfont: { size: isMobile ? 10 : 12 }
      },
      yaxis: {
        anchor: "x",
        domain: [0.7666666667, 1.0],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: false,
        zeroline: false,
        title: {
          font: { size: isMobile ? 11 : 12, color: "#FF3333" },
          text: "<b>Times per year</b>"
        },
        tickfont: { color: "#FF3333", size: isMobile ? 10 : 11 },
        range: [40, 85],
        nticks: 5
      },
      yaxis2: {
        anchor: "x",
        overlaying: "y",
        side: "right",
        showgrid: false,
        showline: false,
        zeroline: false,
        title: {
          font: { size: isMobile ? 11 : 12, color: "#0066CC" },
          text: "<b>Millions of prescriptions</b>"
        },
        tickfont: { color: "#0066CC", size: isMobile ? 10 : 11 },
        range: [150, 420],
        nticks: 5
      },
      xaxis2: {
        anchor: "y3",
        domain: [0.0, 0.94],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: true,
        linewidth: 1,
        linecolor: "rgba(0,0,0,.15)",
        ticks: "outside",
        ticklen: 4,
        tickcolor: "rgba(0,0,0,.15)",
        type: "linear",
        dtick: isTablet ? 4 : 2,
        range: [1999, 2025],
        zeroline: false,
        tickfont: { size: isMobile ? 10 : 12 }
      },
      yaxis3: {
        anchor: "x2",
        domain: [0.3833333333, 0.6166666667],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: false,
        zeroline: false,
        title: {
          font: { size: isMobile ? 11 : 12 },
          text: "<b>Percent married</b>"
        },
        range: [47, 49],
        nticks: 4,
        tickfont: { size: isMobile ? 10 : 11 }
      },
      xaxis3: {
        anchor: "y4",
        domain: [0.0, 0.94],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: true,
        linewidth: 1,
        linecolor: "rgba(0,0,0,.15)",
        ticks: "outside",
        ticklen: 4,
        tickcolor: "rgba(0,0,0,.15)",
        type: "linear",
        dtick: isTablet ? 4 : 2,
        range: [1999, 2025],
        zeroline: false,
        tickfont: { size: isMobile ? 10 : 12 }
      },
      yaxis4: {
        anchor: "x3",
        domain: [0.0, 0.2333333333],
        showgrid: true,
        gridcolor: "rgba(0,0,0,.06)",
        gridwidth: 0.5,
        showline: false,
        zeroline: false,
        title: {
          font: { size: isMobile ? 11 : 12 },
          text: "<b>Hours per day</b>"
        },
        range: [0, 12],
        nticks: 4,
        tickfont: { size: isMobile ? 10 : 11 }
      },
      annotations: [
        {
          font: { 
            color: "#000", 
            size: isMobile ? 13 : 14, 
            family: "Space Grotesk, sans-serif" 
          },
          showarrow: false,
          text: "<b>Sexual frequency has declined as SSRI prescriptions doubled</b>",
          x: 0,
          xanchor: "left",
          xref: "paper",
          y: 1.0,
          yanchor: "bottom",
          yref: "paper"
        },
        {
          font: { 
            color: "#000", 
            size: isMobile ? 13 : 14, 
            family: "Space Grotesk, sans-serif" 
          },
          showarrow: false,
          text: "<b>Marriage rates have remained relatively stable</b>",
          x: 0,
          xanchor: "left",
          xref: "paper",
          y: 0.6166666667,
          yanchor: "bottom",
          yref: "paper"
        },
        {
          font: { 
            color: "#000", 
            size: isMobile ? 13 : 14, 
            family: "Space Grotesk, sans-serif" 
          },
          showarrow: false,
          text: "<b>Daily screen time has quadrupled since 2010</b>",
          x: 0,
          xanchor: "left",
          xref: "paper",
          y: 0.2333333333,
          yanchor: "bottom",
          yref: "paper"
        }
      ],
      font: { 
        family: "Space Grotesk, sans-serif", 
        size: isMobile ? 11 : 12, 
        color: "#0a0a0a" 
      },
      legend: {
        orientation: "h",
        yanchor: "bottom",
        y: 1.12,
        xanchor: "left",
        x: 0.0,
        bgcolor: "rgba(255,255,255,0.85)",
        bordercolor: "rgba(0,0,0,.15)",
        borderwidth: 1,
        font: { size: isMobile ? 11 : 12 }
      },
      margin: { 
        l: isMobile ? 50 : 70, 
        r: isMobile ? 50 : 70, 
        t: 40, 
        b: 40 
      },
      height: isMobile ? 520 : isTablet ? 700 : 950,
      plot_bgcolor: "#fff",
      paper_bgcolor: "#fff",
      showlegend: true,
      hoverlabel: {
        font: { size: isMobile ? 12 : 13, family: "Space Grotesk, sans-serif" },
        bgcolor: "#fff",
        bordercolor: "rgba(0,0,0,.10)"
      },
      hovermode: "x unified",
      doubleClick: "reset"
    };

    try {
      Plotly.newPlot('intimacy-chart', data, layout, { 
        responsive: true, 
        displayModeBar: false, 
        showTips: false 
      });
      this.charts.intimacy = 'intimacy-chart';
    } catch (error) {
      console.error('Failed to create intimacy chart:', error);
    }
  }

  initAnxietyChart() {
    const months = Array.from({ length: 24 }, (_, i) => {
      const m = i * 3;
      return `${2020 + Math.floor(m / 12)}-${String((m % 12) + 1).padStart(2, '0')}`;
    });

    const anxietyAllData = {
      tradwife: months.map((_, i) => Math.min(100, i < 4 ? 15 + i * 8 : i < 10 ? 30 + Math.sin(i * 0.3) * 10 : 40 + (i - 10) * 1.2)),
      measles: months.map((_, i) => i < 16 ? 5 + Math.random() * 3 : 8 + (i - 16) * 15),
      unemployment: months.map((_, i) => i < 4 ? 20 + i * 15 : i < 12 ? 80 - (i - 4) * 5 : 30 - (i - 12) * 0.3),
      eggs: months.map((_, i) => i < 10 ? 35 + Math.sin(i * 0.5) * 8 : i < 17 ? 40 + Math.sin(i * 0.4) * 10 : 50 + (i - 17) * 3),
      gold: months.map((_, i) => 30 + (i * 0.8) + Math.sin(i * 0.2) * 5),
      beef: months.map((_, i) => i < 17 ? 40 + (i * 0.3) : 50 + (i - 17) * 1.5)
    };

    // Initialize all metrics as active
    this.anxietyMetrics.forEach(m => {
      this.activeMetrics[m.key] = true;
    });

    // Create toggle buttons
    const togglesDiv = document.getElementById('anxiety-toggles');
    this.anxietyMetrics.forEach(m => {
      const btn = document.createElement('button');
      btn.className = 'metric-btn active';
      btn.type = 'button';
      btn.textContent = m.name;
      btn.style.backgroundColor = m.color;
      btn.style.color = '#fff';
      btn.setAttribute('role', 'switch');
      btn.setAttribute('aria-pressed', 'true');
      btn.setAttribute('aria-label', `Toggle ${m.name} series`);

      btn.addEventListener('click', () => {
        const isActive = btn.getAttribute('aria-pressed') === 'true';
        btn.setAttribute('aria-pressed', String(!isActive));
        this.activeMetrics[m.key] = !isActive;

        if (!isActive) {
          btn.classList.add('active');
          btn.style.backgroundColor = m.color;
          btn.style.color = '#fff';
        } else {
          btn.classList.remove('active');
          btn.style.backgroundColor = '#e5e7eb';
          btn.style.color = '#4b5563';
        }

        this.updateAnxietyChart(months, anxietyAllData);
      });

      togglesDiv.appendChild(btn);
    });

    this.updateAnxietyChart(months, anxietyAllData);
  }

  updateAnxietyChart(months, anxietyAllData) {
    const isMobile = window.innerWidth < 480;
    const isTablet = window.innerWidth < 768;

    const traces = this.anxietyMetrics
      .filter(m => this.activeMetrics[m.key])
      .map(m => ({
        x: months,
        y: anxietyAllData[m.key],
        name: m.name,
        mode: 'lines',
        line: { color: m.color, width: 3, shape: 'spline' }
      }));

    const layout = {
      xaxis: {
        showgrid: true,
        gridcolor: 'rgba(0,0,0,.06)',
        tickangle: -45,
        nticks: isMobile ? 6 : 12,
        tickfont: { size: isMobile ? 10 : 11 },
        showline: true,
        linewidth: 1,
        linecolor: 'rgba(0,0,0,.15)'
      },
      yaxis: {
        title: {
          text: 'Index (0-100)',
          font: { size: isMobile ? 11 : 12 }
        },
        range: [0, 100],
        nticks: 6,
        tickfont: { size: isMobile ? 10 : 11 },
        gridcolor: 'rgba(0,0,0,.06)'
      },
      annotations: [{
        text: 'All series normalized 0–100 · descriptive, not causal',
        x: 0,
        xref: 'paper',
        xanchor: 'left',
        y: 1.12,
        yref: 'paper',
        yanchor: 'bottom',
        font: {
          size: isMobile ? 10 : 11,
          color: '#333',
          family: 'Space Grotesk, sans-serif'
        },
        showarrow: false
      }],
      margin: {
        l: isMobile ? 50 : 60,
        r: isMobile ? 20 : 40,
        t: 50,
        b: isMobile ? 90 : 80
      },
      height: isMobile ? 500 : isTablet ? 700 : 850,
      plot_bgcolor: '#fff',
      paper_bgcolor: '#fff',
      font: {
        family: 'Space Grotesk, sans-serif',
        size: isMobile ? 11 : 12
      },
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.12,
        font: { size: isMobile ? 11 : 12 }
      },
      hoverlabel: {
        font: {
          size: isMobile ? 12 : 13,
          family: 'Space Grotesk, sans-serif'
        },
        bgcolor: '#fff',
        bordercolor: 'rgba(0,0,0,.10)'
      }
    };

    try {
      Plotly.newPlot('anxiety-chart', traces, layout, {
        responsive: true,
        displayModeBar: false,
        showTips: false
      });
      this.charts.anxiety = 'anxiety-chart';
    } catch (error) {
      console.error('Failed to update anxiety chart:', error);
    }
  }

  handleResize() {
    window.addEventListener('resize', () => {
      const isMobile = window.innerWidth < 480;
      const isTablet = window.innerWidth < 768;
      const h1 = isMobile ? 520 : isTablet ? 700 : 950;
      const h2 = isMobile ? 500 : isTablet ? 700 : 850;

      if (this.charts.intimacy && window.Plotly) {
        Plotly.relayout('intimacy-chart', { height: h1 });
      }
      if (this.charts.anxiety && window.Plotly) {
        Plotly.relayout('anxiety-chart', { height: h2 });
      }
    });
  }
}

// ===== UI CONTROLLER =====
class UIController {
  constructor(audioEngine) {
    this.audioEngine = audioEngine;
  }

  init() {
    this.initMusicToggle();
    this.initVolumeControl();
  }

  initMusicToggle() {
    const toggle = document.getElementById('music-toggle');
    const text = toggle.querySelector('.music-toggle-text');
    const volumeControl = document.getElementById('volume-control');

    toggle.addEventListener('click', async () => {
      await this.audioEngine.start();

      if (this.audioEngine.musicEnabled) {
        toggle.classList.add('active');
        toggle.setAttribute('aria-pressed', 'true');
        text.textContent = 'Music On';
        volumeControl.classList.add('visible');
      } else {
        toggle.classList.remove('active');
        toggle.setAttribute('aria-pressed', 'false');
        text.textContent = 'Music Off';
        volumeControl.classList.remove('visible');
      }
    });
  }

  initVolumeControl() {
  const slider = document.getElementById('volume-slider');
  if (!slider) return;
  slider.addEventListener('input', (e) => {
    this.audioEngine.setVolume(e.target.value);   // <— was this.audioEngine
  });
 }
}
// === Lazy TikTok embed (poster-first, a11y, reduced-motion aware) ===
;(() => {
  const el = document.querySelector('#tiktok-card');
  if (!el) return;

  const url = el.getAttribute('data-tiktok-url') || '';
  const m = url.match(/video\/(\d+)/);
  const videoId = m && m[1];
  if (!videoId) return;

const hydrate = () => {
  if (el.dataset.hydrated === '1') return;
  el.dataset.hydrated = '1';

  const iframe = document.createElement('iframe');
  iframe.src = `https://www.tiktok.com/embed/v2/${videoId}`;
  iframe.allowFullscreen = true;
  iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
  iframe.referrerPolicy = 'origin';
  iframe.loading = 'lazy';
  iframe.title = 'TikTok video';
  
  // Add error handling
  iframe.onerror = () => {
    console.warn('TikTok embed failed to load');
    el.innerHTML = '<p style="padding: 20px; text-align: center;">Video unavailable</p>';
  };
  
  // ... rest of code
};

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!('IntersectionObserver' in window)) {
    hydrate();
    return;
  }

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting || prefersReduced) {
        hydrate();
        io.disconnect();
        break;
      }
    }
  }, { rootMargin: '200px 0px 200px 0px', threshold: 0.01 });

  io.observe(el);
})();


// ===== MAIN APPLICATION =====
class MicrositeApp {
  constructor() {
    // keep constructor light so no ReferenceErrors block init()
    this.loaderEl = document.getElementById('loader');
    this.modules = {};
  }

  async init() {
    try {
      // start loader (fallback if LoaderManager missing)
      if (typeof LoaderManager !== 'undefined') {
        this.modules.loader = new LoaderManager();
        this.modules.loader.start();
      } else {
        this.loaderEl?.classList.remove('hidden'); // ensure visible
      }

      // Wait for libs (only if your DependencyManager exists)
      if (typeof DependencyManager !== 'undefined') {
        const deps = new DependencyManager();
        await deps.waitForDependencies();
      }

      // Init modules only if available to avoid hard crashes
      if (typeof ThreeBackground !== 'undefined') {
        this.modules.three = new ThreeBackground(); this.modules.three.init();
      }
      if (typeof AnimationController !== 'undefined') {
        this.modules.anim = new AnimationController(); this.modules.anim.init();
      }
      if (typeof ChartManager !== 'undefined') {
        this.modules.charts = new ChartManager(); this.modules.charts.init();
      }
      if (typeof CursorManager !== 'undefined' && typeof AudioEngine !== 'undefined') {
        this.modules.audio = new AudioEngine();
        this.modules.cursor = new CursorManager(this.modules.audio); this.modules.cursor.init();
      }
      if (typeof UIController !== 'undefined') {
        this.modules.ui = new UIController(this.modules.audio); this.modules.ui.init();
      }

      // done
      this.complete();
    } catch (err) {
      console.error('Failed to initialize app:', err);
      this.complete(); // still hide loader
    }
  }

  complete() {
    if (this.modules.loader && typeof this.modules.loader.complete === 'function') {
      this.modules.loader.complete();
    } else {
      this.loaderEl?.classList.add('hidden');
    }
  }

  cleanup() {
    try { this.modules.audio?.cleanup?.(); } catch {}
    try { this.modules.cursor?.cleanup?.(); } catch {}
    try { this.modules.three?.cleanup?.(); } catch {}
    try { this.modules.anim?.cleanup?.(); } catch {}
  }
}

// ===== BOOTSTRAP =====
const boot = () => { window.app = new MicrositeApp(); window.app.init(); };
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}

// As a last-resort safety, never leave the loader up on hard errors.
window.addEventListener('error', () => {
  document.getElementById('loader')?.classList.add('hidden');
});
