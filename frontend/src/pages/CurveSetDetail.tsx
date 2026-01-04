import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { getCurveSet, addCurveSeries } from '../api/client';
import Plot from 'react-plotly.js';

const CurveSetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const csId = parseInt(id || '0');

  const { data: curveSet, isLoading } = useQuery({
    queryKey: ['curveSet', csId],
    queryFn: () => getCurveSet(csId),
    enabled: !!csId
  });

  const [inputType, setInputType] = useState<'head' | 'efficiency' | 'power'>('head');
  const [inputText, setInputText] = useState('');

  const addSeriesMutation = useMutation({
    mutationFn: (data: any) => addCurveSeries(csId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curveSet', csId] });
      setInputText('');
    },
  });

  const handleImport = () => {
     // Parse CSV/TSV
     const lines = inputText.trim().split('\n');
     const points = lines.map((line, idx) => {
         const parts = line.trim().split(/[\s,,\t]+/);
         if (parts.length >= 2) {
             return {
                 flow: parseFloat(parts[0]),
                 value: parseFloat(parts[1]),
                 sequence: idx
             };
         }
         return null;
     }).filter(p => p !== null && !isNaN(p.flow) && !isNaN(p.value));

     if (points.length === 0) {
         alert("No valid data found");
         return;
     }

     addSeriesMutation.mutate({
         curve_set_id: csId,
         type: inputType,
         points: points
     });
  };

  if (isLoading) return <div>Loading...</div>;
  if (!curveSet) return <div>Curve Set not found</div>;

  // Prepare plot data
  const plotData: any[] = [];

  const headSeries = curveSet.series.find((s: any) => s.type === 'head');
  if (headSeries) {
      plotData.push({
          x: headSeries.points.map((p: any) => p.flow),
          y: headSeries.points.map((p: any) => p.value),
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Head',
          line: { shape: 'spline' }
      });
  }

  const effSeries = curveSet.series.find((s: any) => s.type === 'efficiency');
  if (effSeries) {
      plotData.push({
          x: effSeries.points.map((p: any) => p.flow),
          y: effSeries.points.map((p: any) => p.value),
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Efficiency',
          yaxis: 'y2',
          line: { shape: 'spline', dash: 'dot' }
      });
  }

  const pwrSeries = curveSet.series.find((s: any) => s.type === 'power');
  if (pwrSeries) {
      plotData.push({
          x: pwrSeries.points.map((p: any) => p.flow),
          y: pwrSeries.points.map((p: any) => p.value),
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Power',
          yaxis: 'y3',
          line: { shape: 'spline', dash: 'dash' }
      });
  }

  return (
    <div className="container mx-auto p-4">
       <div className="mb-4">
           <Link to={`/pumps/${curveSet.pump_id}`} className="text-blue-500 hover:underline">&larr; Back to Pump</Link>
           <h1 className="text-2xl font-bold mt-2">{curveSet.name}</h1>
           <p className="text-sm text-gray-500">Units: {JSON.stringify(curveSet.units)}</p>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           {/* Chart Area */}
           <div className="lg:col-span-2 bg-white p-4 shadow rounded">
               <Plot
                 data={plotData}
                 layout={{
                     title: 'Performance Curves',
                     xaxis: { title: `Flow (${curveSet.units.flow || ''})` },
                     yaxis: { title: `Head (${curveSet.units.head || ''})` },
                     yaxis2: {
                         title: `Efficiency (%)`,
                         overlaying: 'y',
                         side: 'right'
                     },
                     yaxis3: {
                         title: `Power (${curveSet.units.power || ''})`,
                         overlaying: 'y',
                         side: 'right',
                         position: 0.85
                     },
                     autosize: true,
                     height: 500,
                 }}
                 useResizeHandler={true}
                 style={{ width: "100%", height: "100%" }}
               />
           </div>

           {/* Editor Area */}
           <div className="bg-gray-50 p-4 rounded border">
               <h3 className="font-bold mb-4">Edit Curve Data</h3>

               <div className="mb-4">
                   <label className="block text-sm font-medium mb-1">Series Type</label>
                   <select
                     value={inputType}
                     onChange={(e) => setInputType(e.target.value as any)}
                     className="w-full border p-2 rounded"
                   >
                       <option value="head">Head vs Flow</option>
                       <option value="efficiency">Efficiency vs Flow</option>
                       <option value="power">Power vs Flow</option>
                   </select>
               </div>

               <div className="mb-4">
                   <label className="block text-sm font-medium mb-1">Paste Data (Flow, Value)</label>
                   <p className="text-xs text-gray-500 mb-2">Paste from Excel or CSV. First column flow, second value.</p>
                   <textarea
                       className="w-full h-40 p-2 border rounded font-mono text-sm"
                       value={inputText}
                       onChange={(e) => setInputText(e.target.value)}
                       placeholder={`0 100\n100 95\n200 85...`}
                   />
               </div>

               <button
                   onClick={handleImport}
                   className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
               >
                   Save Series
               </button>

               <div className="mt-6 border-t pt-4">
                   <h4 className="font-bold text-sm mb-2">Existing Series</h4>
                   <ul>
                       {curveSet.series.map((s: any) => (
                           <li key={s.id} className="flex justify-between items-center text-sm py-1">
                               <span className="capitalize">{s.type} ({s.points.length} pts)</span>
                               <span className="text-xs text-gray-500">
                                   (Overwritten on save)
                               </span>
                           </li>
                       ))}
                   </ul>
               </div>
           </div>
       </div>
    </div>
  );
};

export default CurveSetDetail;
