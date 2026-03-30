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
    <circle cx="32" cy="32" r="8" fill="#6366F1" opacity="0.3">
        <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.3;0.1;0.3" dur="2s" repeatCount="indefinite"/>
    </circle>
    <circle cx="16" cy="20" r="3" fill="#14B8A6" opacity="0.6">
        <animate attributeName="cy" values="20;16;20" dur="3s" repeatCount="indefinite"/>
    </circle>
    <circle cx="48" cy="24" r="2" fill="#8B5CF6" opacity="0.7">
        <animate attributeName="cy" values="24;28;24" dur="2.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="20" cy="44" r="4" fill="#F97316" opacity="0.5">
        <animate attributeName="r" values="4;6;4" dur="1.8s" repeatCount="indefinite"/>
    </circle>
    <circle cx="44" cy="44" r="2" fill="#06B6D4" opacity="0.6">
        <animate attributeName="cx" values="44;40;44" dur="2.2s" repeatCount="indefinite"/>
    </circle>
    <path d="M32 12L32 20M32 44L32 52M12 32L20 32M44 32L52 32" stroke="#6366F1" stroke-width="1" opacity="0.3">
        <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.5s" repeatCount="indefinite"/>
    </path>
</svg>
