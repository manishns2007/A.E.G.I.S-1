import { useEffect, useState } from 'react';
import { ReactFlow, useNodesState, useEdgesState, Controls, Background } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { getGraphData } from '../services/api';

const Graph = ({ caseId }: { caseId: string }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const data = await getGraphData(caseId);
        if (!data || !data.nodes) return;
        
        const otherNodes = data.nodes.filter((n: any) => n.type !== 'case');
        const formattedNodes = data.nodes.map((node: any) => {
          if (node.type === 'case') {
            return {
              id: node.id,
              data: { label: node.label },
              position: { x: 400, y: 300 },
              style: {
                background: '#00d2ff',
                color: '#05070e',
                border: '2px solid #38bdf8',
                fontWeight: 'bold',
                padding: '12px 18px',
                borderRadius: '8px',
                fontSize: '13px',
                boxShadow: '0 0 20px rgba(0, 210, 255, 0.4)'
              }
            };
          }
          
          const idx = otherNodes.findIndex((n: any) => n.id === node.id);
          const total = otherNodes.length || 1;
          const radius = 220;
          const angle = (idx / total) * 2 * Math.PI;

          let bg = '#1e293b';
          let border = '#3b82f6';
          let color = '#f8fafc';

          if (node.type === 'vector_privacy') {
            bg = 'rgba(0, 255, 157, 0.15)';
            border = '#00ff9d';
            color = '#00ff9d';
          } else if (node.type === 'vector_physics') {
            bg = 'rgba(255, 183, 3, 0.15)';
            border = '#ffb703';
            color = '#ffb703';
          } else if (node.type === 'vector_optical') {
            bg = 'rgba(192, 132, 252, 0.15)';
            border = '#c084fc';
            color = '#c084fc';
          } else if (node.type === 'custody_seal') {
            bg = 'rgba(96, 165, 250, 0.15)';
            border = '#60a5fa';
            color = '#60a5fa';
          }

          return {
            id: node.id,
            data: { label: node.label },
            position: { 
              x: 400 + radius * Math.cos(angle), 
              y: 300 + radius * Math.sin(angle) 
            },
            style: { 
              background: bg, 
              color: color, 
              border: `1px solid ${border}`,
              padding: '8px 14px',
              borderRadius: '6px',
              fontSize: '11px',
              fontFamily: 'monospace',
              fontWeight: '600'
            }
          };
        });
        
        const formattedEdges = data.edges.map((edge: any, idx: number) => ({
          id: `e-${idx}`,
          source: edge.source,
          target: edge.target,
          animated: true,
          label: edge.label || '',
          style: { stroke: '#00d2ff', strokeWidth: 1.5 },
          labelStyle: { fill: '#94a3b8', fontSize: 9 }
        }));
        
        setNodes(formattedNodes);
        setEdges(formattedEdges);
      } catch (err) {
        console.error("Failed to load graph data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGraph();
  }, [caseId, setNodes, setEdges]);

  if (loading) return <div className="h-full flex items-center justify-center text-secondary">Loading Intelligence Graph...</div>;

  return (
    <div style={{ width: '100%', height: '500px' }} className="border border-border rounded-lg bg-background overflow-hidden relative">
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        onNodesChange={onNodesChange} 
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.3 }}
      >
        <Controls />
        <Background color="#1e293b" gap={16} />
      </ReactFlow>
    </div>
  );
};

export default Graph;
