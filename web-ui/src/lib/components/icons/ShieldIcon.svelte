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
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
    <path d="M9 12l2 2 4-4"/>
    <circle cx="12" cy="10" r="1" fill="currentColor" opacity="0.5"/>
    <path d="M8 14c1 1 3 1.5 4 1.5s3-.5 4-1.5"/>
</svg>
