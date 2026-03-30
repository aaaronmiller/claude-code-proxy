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
    style="color: var(--warning)"
>
    <circle cx="12" cy="8" r="4"/>
    <circle cx="6" cy="14" r="3"/>
    <circle cx="18" cy="14" r="3"/>
    <path d="M12 12v4"/>
    <path d="M9 17l-1 3"/>
    <path d="M15 17l1 3"/>
    <path d="M12 16v4"/>
    <circle cx="12" cy="8" r="2" fill="currentColor" opacity="0.3"/>
</svg>
