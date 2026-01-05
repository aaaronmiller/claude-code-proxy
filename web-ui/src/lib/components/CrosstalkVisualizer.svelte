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

    // Enhanced props for full topology support
    let {
        models = [],
        paradigm = "relay",
        topology = { type: "ring", order: [], center: 1, spokes: [] }
    } = $props();

    let nodes = $state<Node[]>([]);
    let edges = $state<Edge[]>([]);

    // Color schemes based on paradigm
    const colorSchemes = {
        relay: { node: "#06ffd4", edge: "#06ffd4", bg: "rgba(6, 255, 212, 0.1)" },
        memory: { node: "#22c55e", edge: "#22c55e", bg: "rgba(34, 197, 94, 0.1)" },
        debate: { node: "#ec4899", edge: "#ec4899", bg: "rgba(236, 72, 153, 0.1)" },
        report: { node: "#f59e0b", edge: "#f59e0b", bg: "rgba(245, 158, 11, 0.1)" }
    };

    function getColors(paradigm: string) {
        return colorSchemes[paradigm as keyof typeof colorSchemes] || colorSchemes.relay;
    }

    $effect(() => {
        const generatedNodes: Node[] = [];
        const generatedEdges: Edge[] = [];
        const colors = getColors(paradigm);

        // Layout parameters
        const centerX = 300;
        const centerY = 150;
        const radius = 120;

        if (topology.type === "ring") {
            // Circular layout - Reason Flow style
            models.forEach((model: string, i: number) => {
                const angle = (2 * Math.PI * i / models.length) - (Math.PI / 2);
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);

                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: {
                        label: `AI${i+1}`,
                        sublabel: model.split('/').pop() || model,
                        tier: i === 0 ? "lead" : "participant"
                    },
                    position: { x, y },
                    class: "crosstalk-node",
                });

                // Ring flow edges
                if (models.length > 1) {
                    const next = (i + 1) % models.length;
                    generatedEdges.push({
                        id: `edge-${i}-${next}`,
                        source: `node-${i}`,
                        target: `node-${next}`,
                        animated: true,
                        type: "smoothstep",
                        style: `stroke: ${colors.edge}; stroke-width: 2;`,
                        label: `${i}→${next}`,
                        labelStyle: `fill: ${colors.edge}; font-size: 10px; font-family: monospace;`,
                    });
                }
            });
        } else if (topology.type === "star") {
            // Star layout - center + spokes
            const centerIndex = topology.center - 1;
            if (centerIndex >= 0 && centerIndex < models.length) {
                // Center node
                generatedNodes.push({
                    id: `node-center`,
                    type: "default",
                    data: {
                        label: `CENTER`,
                        sublabel: models[centerIndex].split('/').pop() || models[centerIndex],
                        tier: "center"
                    },
                    position: { x: centerX, y: centerY },
                    class: "crosstalk-node center",
                });

                // Spokes
                const spokes = topology.spokes.length > 0
                    ? topology.spokes
                    : models.map((_, i) => i + 1).filter(i => i !== topology.center);

                spokes.forEach((spoke, i) => {
                    const spokeIndex = spoke - 1;
                    if (spokeIndex >= 0 && spokeIndex < models.length && spokeIndex !== centerIndex) {
                        const angle = (2 * Math.PI * i / spokes.length);
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);

                        generatedNodes.push({
                            id: `node-${spokeIndex}`,
                            type: "default",
                            data: {
                                label: `AI${spoke}`,
                                sublabel: models[spokeIndex].split('/').pop() || models[spokeIndex],
                                tier: "spoke"
                            },
                            position: { x, y },
                            class: "crosstalk-node",
                        });

                        // Bidirectional edges for star
                        generatedEdges.push({
                            id: `edge-center-${spokeIndex}`,
                            source: `node-center`,
                            target: `node-${spokeIndex}`,
                            animated: true,
                            type: "smoothstep",
                            style: `stroke: ${colors.edge}; stroke-width: 2;`,
                        });
                        generatedEdges.push({
                            id: `edge-${spokeIndex}-center`,
                            source: `node-${spokeIndex}`,
                            target: `node-center`,
                            animated: true,
                            type: "smoothstep",
                            style: `stroke: ${colors.edge}; stroke-width: 2; stroke-dasharray: 4; opacity: 0.5`,
                        });
                    }
                });
            }
        } else if (topology.type === "mesh") {
            // Mesh layout - all to all
            const cols = 3;
            const startX = 100;
            const startY = 80;
            const spacingX = 180;
            const spacingY = 120;

            models.forEach((model: string, i: number) => {
                const x = startX + (i % cols) * spacingX;
                const y = startY + Math.floor(i / cols) * spacingY;

                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: {
                        label: `AI${i+1}`,
                        sublabel: model.split('/').pop() || model,
                        tier: "mesh"
                    },
                    position: { x, y },
                    class: "crosstalk-node",
                });

                // All-to-all edges (with opacity for readability)
                models.forEach((_, j) => {
                    if (i !== j) {
                        generatedEdges.push({
                            id: `edge-${i}-${j}`,
                            source: `node-${i}`,
                            target: `node-${j}`,
                            animated: true,
                            type: "straight",
                            style: `stroke: ${colors.edge}; stroke-width: 1; opacity: 0.3;`,
                        });
                    }
                });
            });
        } else if (topology.type === "chain") {
            // Linear chain
            const startX = 100;
            const startY = centerY;
            const spacingX = 180;

            models.forEach((model: string, i: number) => {
                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: {
                        label: `AI${i+1}`,
                        sublabel: model.split('/').pop() || model,
                        tier: i === 0 ? "start" : i === models.length - 1 ? "end" : "chain"
                    },
                    position: { x: startX + i * spacingX, y: startY },
                    class: "crosstalk-node",
                });

                if (i < models.length - 1) {
                    generatedEdges.push({
                        id: `edge-${i}-${i+1}`,
                        source: `node-${i}`,
                        target: `node-${i + 1}`,
                        animated: true,
                        style: `stroke: ${colors.edge}; stroke-width: 2;`,
                    });
                }
            });
        } else {
            // Fallback: Simple linear
            const startX = 100;
            const spacingX = 180;

            models.forEach((model: string, i: number) => {
                generatedNodes.push({
                    id: `node-${i}`,
                    type: "default",
                    data: {
                        label: `AI${i+1}`,
                        sublabel: model.split('/').pop() || model,
                        tier: "default"
                    },
                    position: { x: startX + i * spacingX, y: centerY },
                    class: "crosstalk-node",
                });

                if (i < models.length - 1) {
                    generatedEdges.push({
                        id: `edge-${i}-${i+1}`,
                        source: `node-${i}`,
                        target: `node-${i + 1}`,
                        animated: true,
                        style: `stroke: ${colors.edge}; stroke-width: 2;`,
                    });
                }
            });
        }

        nodes = generatedNodes;
        edges = generatedEdges;
    });
</script>

<div
    class="h-[350px] w-full border border-cyber-border rounded-lg bg-black/40 overflow-hidden relative"
>
    <SvelteFlow
        {nodes}
        {edges}
        fitView
        class="bg-transparent"
        minZoom={0.3}
        maxZoom={1.5}
        initialZoom={0.8}
    >
        <Controls showInteractive={false} />
        <Background bgColor="#222" gap={20} size={1} />
    </SvelteFlow>
</div>

<style>
    :global(.crosstalk-node) {
        background: rgba(15, 15, 25, 0.95) !important;
        border: 1px solid #444 !important;
        color: #e4e4e7 !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 10px !important;
        width: 140px !important;
        text-align: center !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(4px) !important;
        transition: all 0.2s ease !important;
    }

    :global(.crosstalk-node:hover) {
        transform: scale(1.05) !important;
        border-color: #a855f7 !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.4) !important;
    }

    :global(.crosstalk-node.center) {
        border: 2px solid #a855f7 !important;
        background: rgba(80, 25, 120, 0.3) !important;
        font-weight: bold !important;
        font-size: 11px !important;
    }

    :global(.svelte-flow__attribution) {
        background: transparent !important;
        opacity: 0.1;
    }

    :global(.svelte-flow__controls) {
        background: rgba(15, 15, 25, 0.8) !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }

    :global(.svelte-flow__controls button) {
        background: rgba(40, 40, 60, 0.8) !important;
        border: 1px solid #555 !important;
        color: #e4e4e7 !important;
    }

    :global(.svelte-flow__controls button:hover) {
        background: rgba(60, 60, 90, 0.9) !important;
        border-color: #a855f7 !important;
    }
</style>
