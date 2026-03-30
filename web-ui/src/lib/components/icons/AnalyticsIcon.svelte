<script>
    let { size = 24, className = '' } = $props();
</script>

<svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    stroke-width="1.5" 
    stroke-linecap="round" 
    stroke-linejoin="round"
    class={className}
    style="color: var(--success)"
>
    <path d="M3 3v18h18"/>
    <path d="M7 16l4-4 4 4 5-6"/>
    <circle cx="18" cy="9" r="2"/>
</svg>
