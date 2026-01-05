<script lang="ts">
    import {
        SvelteFlow,
        Background,
        Controls,
        Position,
        type Node,
        type Edge,
    } from "@xyflow/svelte";
    import "@xyflow/svelte/dist/style.css";

    let { models = [], paradigm = "relay" } = $props();

    let nodes = $state<Node[]>([]);
    let edges = $state<Edge[]>([]);

    $effect(() => {
        const generatedNodes: Node[] = [];
        const generatedEdges: Edge[] = [];

        // Define layout parameters
        const startX = 50;
        const startY = 100;
        const spacingX = 250;
        const spacingY = 100;

        if (paradigm === "relay" || paradigm === "sequential") {
            // Sequential Layout: A -> B -> C
            models.forEach((model: string, i: number) => {
                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: { label: model },
                    position: { x: startX + i * spacingX, y: startY },
                    class: "cyber-node",
                });

                if (i < models.length - 1) {
                    generatedEdges.push({
                        id: `edge-${i}`,
                        source: `node-${i}`,
                        target: `node-${i + 1}`,
                        animated: true,
                        style: "stroke: #06ffd4; stroke-width: 2;",
                    });
                }
            });
        } else if (paradigm === "debate") {
            // Debate Layout: A <-> B (Side by side)
            models.forEach((model: string, i: number) => {
                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: { label: model },
                    position: { x: startX + i * spacingX, y: startY },
                    class: "cyber-node",
                });
            });

            // Add bidirectional edges
            for (let i = 0; i < models.length; i++) {
                for (let j = i + 1; j < models.length; j++) {
                    generatedEdges.push({
                        id: `edge-${i}-${j}`,
                        source: `node-${i}`,
                        target: `node-${j}`,
                        animated: true,
                        style: "stroke: #ec4899; stroke-width: 2;",
                    });
                    generatedEdges.push({
                        id: `edge-${j}-${i}`,
                        source: `node-${j}`,
                        target: `node-${i}`,
                        animated: true,
                        style: "stroke: #ec4899; stroke-width: 2;",
                    });
                }
            }
        } else {
            // Fallback Linear
            models.forEach((model: string, i: number) => {
                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: { label: model },
                    position: {
                        x: startX + i * spacingX,
                        y: startY + (i % 2) * 30,
                    },
                    class: "cyber-node",
                });
            });
        }

        nodes = generatedNodes;
        edges = generatedEdges;
    });
</script>

<div
    class="h-[300px] w-full border border-cyber-border rounded-lg bg-black/40 overflow-hidden relative"
>
    <SvelteFlow {nodes} {edges} fitView class="bg-transparent">
        <Controls />
        <Background bgColor="#333" gap={20} size={1} />
    </SvelteFlow>
</div>

<style>
    :global(.cyber-node) {
        background: rgba(20, 18, 40, 0.9) !important;
        border: 1px solid #06ffd4 !important;
        color: #fff !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-family: monospace !important;
        font-size: 11px !important;
        width: 180px !important;
        text-align: center !important;
        box-shadow: 0 0 10px rgba(6, 255, 212, 0.2) !important;
    }

    :global(.svelte-flow__attribution) {
        background: transparent !important;
        opacity: 0.2;
    }
</style>
