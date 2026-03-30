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
    style="color: var(--accent-default)"
>
    <path d="M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0 1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 5.28.55"/>
    <path d="M12 4.5a2.5 2.5 0 0 1 4.96-.46 2.5 2.5 0 0 1 1.98 3 2.5 2.5 0 0 1-1.32 4.24 3 3 0 0 1-.34 5.58 2.5 2.5 0 0 1-5.28.55"/>
    <path d="M12 4.5v16"/>
    <path d="M12 8.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0 1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 5.28.55"/>
    <circle cx="12" cy="12" r="2"/>
    <circle cx="12" cy="8" r="1.5" fill="currentColor" opacity="0.5"/>
    <circle cx="12" cy="16" r="1.5" fill="currentColor" opacity="0.5"/>
    <circle cx="8" cy="12" r="1" fill="currentColor" opacity="0.3"/>
    <circle cx="16" cy="12" r="1" fill="currentColor" opacity="0.3"/>
</svg>
