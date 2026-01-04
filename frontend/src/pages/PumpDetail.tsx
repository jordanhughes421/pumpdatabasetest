import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { getPump, createCurveSet, deleteCurveSet } from '../api/client';

const PumpDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const pumpId = parseInt(id || '0');

  const { data: pump, isLoading } = useQuery({
    queryKey: ['pump', pumpId],
    queryFn: () => getPump(pumpId),
    enabled: !!pumpId
  });

  console.log("PumpDetail render:", { pump, isLoading });

  const [newCurveName, setNewCurveName] = useState('');

  const createCurveMutation = useMutation({
    mutationFn: createCurveSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pump', pumpId] });
      setNewCurveName('');
    },
  });

  const deleteCurveMutation = useMutation({
    mutationFn: deleteCurveSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pump', pumpId] });
    },
  });

  const handleCreateCurve = (e: React.FormEvent) => {
    e.preventDefault();
    if (newCurveName) {
      createCurveMutation.mutate({
        name: newCurveName,
        pump_id: pumpId,
        units: { flow: 'gpm', head: 'ft', efficiency: '%', power: 'hp' }
      });
    }
  };

  if (isLoading) return <div className="p-4">Loading...</div>;
  if (!pump) return <div className="p-4">Pump not found</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6">
        <Link to="/" className="text-blue-500 hover:underline mb-4 inline-block">&larr; Back to Library</Link>
        <h1 className="text-3xl font-bold text-gray-900">{pump.manufacturer} {pump.model}</h1>
        <div className="text-gray-600 mt-2">
           Metadata: <pre className="inline text-xs bg-gray-100 p-1 rounded">{JSON.stringify(pump.meta_data, null, 2)}</pre>
        </div>
      </div>

      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Curve Sets</h2>
            <form onSubmit={handleCreateCurve} className="flex gap-2">
                <input
                    type="text"
                    placeholder="New Curve Set Name"
                    className="border rounded px-2 py-1"
                    value={newCurveName}
                    onChange={(e) => setNewCurveName(e.target.value)}
                />
                <button type="submit" className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700">Add</button>
            </form>
        </div>

        <div className="grid gap-4">
            {pump.curve_sets?.map((cs: any) => (
                <div key={cs.id} className="border rounded p-4 shadow-sm hover:shadow-md transition">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-bold text-blue-800">
                            <Link to={`/curve-sets/${cs.id}`}>{cs.name}</Link>
                        </h3>
                        <div className="text-sm text-gray-500">
                             Units: {JSON.stringify(cs.units)}
                        </div>
                        <button
                            onClick={() => { if(confirm('Delete curve set?')) deleteCurveMutation.mutate(cs.id) }}
                            className="text-red-500 text-sm hover:underline"
                        >
                            Delete
                        </button>
                    </div>
                </div>
            ))}
            {pump.curve_sets?.length === 0 && <p className="text-gray-500 italic">No curve sets defined.</p>}
        </div>
      </div>
    </div>
  );
};

export default PumpDetail;
