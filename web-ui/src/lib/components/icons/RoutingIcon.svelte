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
>
    <circle cx="12" cy="12" r="3"/>
    <circle cx="4" cy="6" r="2"/>
    <circle cx="20" cy="6" r="2"/>
    <circle cx="4" cy="18" r="2"/>
    <circle cx="20" cy="18" r="2"/>
    <path d="M9.5 10.5L6 8"/>
    <path d="M14.5 10.5L18 8"/>
    <path d="M9.5 13.5L6 16"/>
    <path d="M14.5 13.5L18 16"/>
    <path d="M12 9v3"/>
    <path d="M6 8l-2 3"/>
    <path d="M18 8l2 3"/>
    <path d="M6 16l-2-3"/>
    <path d="M18 16l2-3"/>
</svg>
