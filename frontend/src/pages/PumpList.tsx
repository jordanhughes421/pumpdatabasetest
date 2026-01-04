import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPumps, deletePump } from '../api/client';
import { Link } from 'react-router-dom';

const PumpList: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: pumps, isLoading, error } = useQuery({ queryKey: ['pumps'], queryFn: getPumps });

  const deleteMutation = useMutation({
    mutationFn: deletePump,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pumps'] });
    },
  });

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this pump?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) return <div className="p-4">Loading pumps...</div>;
  if (error) return <div className="p-4 text-red-500">Error loading pumps</div>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Pump Library</h1>
        <Link to="/pumps/new" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Add New Pump
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Manufacturer</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {pumps.map((pump: any) => (
              <tr key={pump.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{pump.manufacturer}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{pump.model}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(pump.created_at).toLocaleDateString()}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link to={`/pumps/${pump.id}`} className="text-indigo-600 hover:text-indigo-900 mr-4">Details</Link>
                  <button onClick={() => handleDelete(pump.id)} className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
            {pumps.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">No pumps found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PumpList;
