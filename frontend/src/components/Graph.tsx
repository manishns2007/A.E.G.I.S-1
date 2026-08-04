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
        
        // Basic layout algorithm
        const formattedNodes = data.nodes.map((node: any, idx: number) => {
          // Put the central case node in the middle
          if (node.type === 'case') {
            return {
              id: node.id,
              data: { label: node.label },
              position: { x: 400, y: 300 },
              style: { background: '#00d2ff', color: '#000', border: 'none', fontWeight: 'bold' }
            };
          }
          
          // Distribute other nodes in a circle
          const radius = 250;
          const angle = (idx / (data.nodes.length - 1)) * 2 * Math.PI;
          return {
            id: node.id,
            data: { label: node.label },
            position: { 
              x: 400 + radius * Math.cos(angle), 
              y: 300 + radius * Math.sin(angle) 
            },
            style: { background: '#162032', color: '#e2e8f0', borderColor: '#ffb703' }
          };
        });
        
        const formattedEdges = data.edges.map((edge: any, idx: number) => ({
          id: `e-${idx}`,
          source: edge.source,
          target: edge.target,
          animated: true,
          style: { stroke: '#94a3b8' }
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
    <div style={{ width: '100%', height: '500px' }} className="border border-border rounded-lg bg-background">
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        onNodesChange={onNodesChange} 
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Controls />
        <Background color="#2a364f" gap={16} />
      </ReactFlow>
    </div>
  );
};

export default Graph;
