<script>
    let { variant = 'default' } = $props();
</script>

<div class="hero-bg" class:variant-aurora={variant === 'aurora'} class:variant-ember={variant === 'ember'} class:variant-synthwave={variant === 'synthwave'}>
    <!-- Grid overlay -->
    <div class="hero-grid"></div>
    
    <!-- Animated orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    
    <!-- Floating particles -->
    <div class="particle p1"></div>
    <div class="particle p2"></div>
    <div class="particle p3"></div>
    <div class="particle p4"></div>
    
    <!-- Circuit lines -->
    <svg class="circuit-lines" viewBox="0 0 400 200" preserveAspectRatio="none">
        <path class="circuit circuit-1" d="M0,100 Q100,50 200,100 T400,100" />
        <path class="circuit circuit-2" d="M0,150 Q100,100 200,150 T400,150" />
        <path class="circuit circuit-3" d="M50,0 Q100,100 150,200" />
        <path class="circuit circuit-4" d="M350,0 Q300,100 250,200" />
    </svg>
</div>

<style>
    .hero-bg {
        position: absolute;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        border-radius: inherit;
    }

    .hero-grid {
        position: absolute;
        inset: 0;
        background-image: 
            linear-gradient(var(--border-default) 1px, transparent 1px),
            linear-gradient(90deg, var(--border-default) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.3;
        mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 40%, transparent 100%);
    }

    .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.4;
        animation: float 20s ease-in-out infinite;
    }

    .orb-1 {
        width: 300px;
        height: 300px;
        background: var(--primary-default);
        top: -100px;
        right: -50px;
        animation-delay: 0s;
    }

    .orb-2 {
        width: 200px;
        height: 200px;
        background: var(--accent-default);
        bottom: -50px;
        left: -50px;
        animation-delay: -5s;
    }

    .orb-3 {
        width: 150px;
        height: 150px;
        background: var(--chart-3, purple);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation-delay: -10s;
    }

    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: var(--accent-default);
        border-radius: 50%;
        opacity: 0;
        animation: particle-float 15s ease-in-out infinite;
    }

    .p1 { top: 20%; left: 20%; animation-delay: 0s; }
    .p2 { top: 60%; left: 80%; animation-delay: -3s; }
    .p3 { top: 80%; left: 30%; animation-delay: -6s; }
    .p4 { top: 40%; left: 60%; animation-delay: -9s; }

    .circuit-lines {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        opacity: 0.15;
    }

    .circuit {
        fill: none;
        stroke: var(--accent-default);
        stroke-width: 1;
        stroke-dasharray: 200;
        stroke-dashoffset: 200;
        animation: circuit-draw 8s ease-in-out infinite;
    }

    .circuit-2 { animation-delay: -2s; }
    .circuit-3 { animation-delay: -4s; }
    .circuit-4 { animation-delay: -6s; }

    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(20px, -20px) scale(1.05); }
        50% { transform: translate(-10px, 10px) scale(0.95); }
        75% { transform: translate(15px, 15px) scale(1.02); }
    }

    @keyframes particle-float {
        0% { opacity: 0; transform: translate(0, 0); }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { opacity: 0; transform: translate(30px, -30px); }
    }

    @keyframes circuit-draw {
        0% { stroke-dashoffset: 200; opacity: 0; }
        20% { opacity: 0.3; }
        80% { opacity: 0.3; }
        100% { stroke-dashoffset: 0; opacity: 0; }
    }

    /* Variant: Aurora */
    .variant-aurora .orb-1 { background: linear-gradient(135deg, hsl(230, 70%, 55%), hsl(170, 75%, 55%)); }
    .variant-aurora .orb-2 { background: hsl(280, 60%, 60%); }
    .variant-aurora .circuit { stroke: hsl(170, 75%, 55%); }

    /* Variant: Ember */
    .variant-ember .orb-1 { background: linear-gradient(135deg, hsl(25, 75%, 52%), hsl(200, 70%, 50%)); }
    .variant-ember .orb-2 { background: hsl(45, 80%, 55%); }
    .variant-ember .circuit { stroke: hsl(25, 90%, 55%); }

    /* Variant: Synthwave */
    .variant-synthwave .orb-1 { background: linear-gradient(135deg, hsl(280, 60%, 60%), hsl(320, 80%, 60%)); }
    .variant-synthwave .orb-2 { background: hsl(180, 80%, 50%); }
    .variant-synthwave .circuit { stroke: hsl(320, 80%, 60%); }
</style>
