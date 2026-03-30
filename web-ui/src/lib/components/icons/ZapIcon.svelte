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
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    <path d="M11 2v12"/>
    <path d="M13 2l-1 12"/>
    <circle cx="16" cy="11" r="1" fill="currentColor" opacity="0.4"/>
</svg>
