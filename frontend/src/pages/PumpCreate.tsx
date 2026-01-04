import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createPump } from '../api/client';
import { useNavigate } from 'react-router-dom';

const PumpCreate: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [metadata, setMetadata] = useState('{}');

  const mutation = useMutation({
    mutationFn: createPump,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pumps'] });
      navigate('/');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const meta = JSON.parse(metadata);
        mutation.mutate({ manufacturer, model, meta_data: meta });
    } catch (err) {
        alert("Invalid JSON in metadata");
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Create New Pump</h1>
      <form onSubmit={handleSubmit} className="max-w-lg bg-white p-6 rounded shadow">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">Manufacturer</label>
          <input
            type="text"
            value={manufacturer}
            onChange={(e) => setManufacturer(e.target.value)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">Model</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          />
        </div>
        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2">Metadata (JSON)</label>
          <textarea
            value={metadata}
            onChange={(e) => setMetadata(e.target.value)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32 font-mono"
          />
        </div>
        <div className="flex items-center justify-between">
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Create Pump
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="inline-block align-baseline font-bold text-sm text-blue-500 hover:text-blue-800"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default PumpCreate;
