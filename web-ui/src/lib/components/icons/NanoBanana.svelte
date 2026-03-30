<script lang="ts">
    interface Props {
        size?: number;
        class?: string;
    }

    let { size = 24, class: className = "" }: Props = $props();
</script>

<svg 
    width={size} 
    height={size} 
    viewBox="0 0 64 64" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    class={className}
>
    <defs>
        <linearGradient id="bananaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#FFE135;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#F4C430;stop-opacity:1" />
        </linearGradient>
        <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    <path 
        d="M44 8C38 8 32 14 28 24C24 34 22 44 26 52C30 60 40 62 50 56C60 50 62 36 58 24C54 12 50 8 44 8Z" 
        fill="url(#bananaGrad)"
        filter="url(#glow)"
    />
    <path 
        d="M28 20C32 12 40 8 48 12" 
        stroke="#8B6914" 
        stroke-width="2" 
        stroke-linecap="round"
        opacity="0.6"
    />
    <circle cx="46" cy="16" r="3" fill="#FF6B6B" opacity="0.8">
        <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="36" cy="40" r="2" fill="#4ECDC4" opacity="0.6">
        <animate attributeName="r" values="2;3;2" dur="1.5s" repeatCount="indefinite"/>
    </circle>
</svg>
