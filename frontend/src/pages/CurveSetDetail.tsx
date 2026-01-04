import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { getCurveSet, addCurveSeries, validateCurvePoints, evaluateSeries } from '../api/client';
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

  // Validation state
  const [validationResult, setValidationResult] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Plot state
  const [showFitted, setShowFitted] = useState(true);
  const [showRaw, setShowRaw] = useState(true);

  // Duty Point state
  const [dutyFlow, setDutyFlow] = useState<string>('');
  const [dutyHead, setDutyHead] = useState<string>('');
  const [dutyResult, setDutyResult] = useState<any>(null);

  const addSeriesMutation = useMutation({
    mutationFn: (data: any) => addCurveSeries(csId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curveSet', csId] });
      setInputText('');
      setValidationResult(null);
    },
    onError: (error: any) => {
        alert("Failed to save: " + JSON.stringify(error.response?.data || error.message));
    }
  });

  const validateMutation = useMutation({
      mutationFn: (data: any) => validateCurvePoints(data),
      onSuccess: (data) => {
          setValidationResult(data);
      },
      onError: (error: any) => {
          console.error(error);
      }
  });

  const evaluateMutation = useMutation({
      mutationFn: (data: any) => evaluateSeries(data.seriesId, data.flow, data.head),
      onSuccess: (data) => {
          setDutyResult((prev: any) => ({ ...prev, ...data.predictions, warnings: data.warnings, residuals: data.residuals, extrapolation: data.extrapolation }));
      }
  });

  useEffect(() => {
      // Debounced validation
      const handler = setTimeout(() => {
          if (inputText.trim()) {
              const points = parsePoints(inputText);
              if (points.length > 0) {
                  setIsValidating(true);
                  validateMutation.mutate({ curve_type: inputType, points: points }, {
                      onSettled: () => setIsValidating(false)
                  });
              } else {
                  setValidationResult(null);
              }
          } else {
              setValidationResult(null);
          }
      }, 500);

      return () => clearTimeout(handler);
  }, [inputText, inputType]);

  const parsePoints = (text: string) => {
     const lines = text.trim().split('\n');
     return lines.map((line, idx) => {
         const parts = line.trim().split(/[\s,,\t]+/);
         if (parts.length >= 2) {
             const flow = parseFloat(parts[0]);
             const value = parseFloat(parts[1]);
             // Allow NaNs here so validation backend catches them if user typed garbage
             if (isNaN(flow) || isNaN(value)) {
                 return { flow: isNaN(flow) ? parts[0] : flow, value: isNaN(value) ? parts[1] : value, sequence: idx };
             }
             return { flow, value, sequence: idx };
         }
         return null;
     }).filter(p => p !== null);
  };

  const handleSave = () => {
      if (validationResult?.blocking_errors?.length > 0) return;
      const points = validationResult?.normalized_points || parsePoints(inputText).filter((p: any) => !isNaN(p.flow) && !isNaN(p.value));
      addSeriesMutation.mutate({
         curve_set_id: csId,
         type: inputType,
         points: points
     });
  };

  const handleEvaluate = () => {
      setDutyResult({});
      const flow = parseFloat(dutyFlow);
      const head = dutyHead ? parseFloat(dutyHead) : null;
      if (isNaN(flow)) return;

      if (curveSet) {
          curveSet.series.forEach((s: any) => {
              evaluateMutation.mutate({ seriesId: s.id, flow, head: s.type === 'head' ? head : null });
          });
      }
  };

  if (isLoading) return <div>Loading...</div>;
  if (!curveSet) return <div>Curve Set not found</div>;

  // Prepare plot data
  const plotData: any[] = [];

  const addPlotTraces = (series: any, name: string, yaxis: string = 'y', color: string) => {
      // Raw points
      if (showRaw) {
          plotData.push({
              x: series.points.map((p: any) => p.flow),
              y: series.points.map((p: any) => p.value),
              type: 'scatter',
              mode: 'markers',
              name: `${name} (Raw)`,
              yaxis: yaxis,
              marker: { color: color, size: 8, symbol: 'circle-open' }
          });
      }

      // Fitted curve
      // If we have coeffs, we can generate points.
      if (showFitted && series.fit_model_type) {
          const minQ = series.data_range?.min_q || 0;
          const maxQ = series.data_range?.max_q || 0;
          // Generate 100 points
          const step = (maxQ - minQ) / 100;
          const xFit = [];
          const yFit = [];
          if (step > 0) {
            for (let x = minQ; x <= maxQ; x += step) {
                xFit.push(x);
                // Evaluate polynomial
                if (series.fit_model_type.startsWith('polynomial')) {
                    const coeffs = series.fit_params?.coeffs;
                    if (coeffs) {
                        // coeffs are [a, b, c] for ax^2 + bx + c (highest degree first)
                        let y = 0;
                        coeffs.forEach((c: number, i: number) => {
                            y += c * Math.pow(x, coeffs.length - 1 - i);
                        });
                        yFit.push(y);
                    }
                }
            }
            plotData.push({
                x: xFit,
                y: yFit,
                type: 'scatter',
                mode: 'lines',
                name: `${name} (Fit)`,
                yaxis: yaxis,
                line: { color: color, shape: 'spline' }
            });
          }
      }
  };

  const headSeries = curveSet.series.find((s: any) => s.type === 'head');
  if (headSeries) addPlotTraces(headSeries, 'Head', 'y', 'blue');

  const effSeries = curveSet.series.find((s: any) => s.type === 'efficiency');
  if (effSeries) addPlotTraces(effSeries, 'Efficiency', 'y2', 'green');

  const pwrSeries = curveSet.series.find((s: any) => s.type === 'power');
  if (pwrSeries) addPlotTraces(pwrSeries, 'Power', 'y3', 'red');

  return (
    <div className="container mx-auto p-4">
       <div className="mb-4">
           <Link to={`/pumps/${curveSet.pump_id}`} className="text-blue-500 hover:underline">&larr; Back to Pump</Link>
           <h1 className="text-2xl font-bold mt-2">{curveSet.name}</h1>
           <p className="text-sm text-gray-500">Units: {JSON.stringify(curveSet.units)}</p>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           {/* Chart Area */}
           <div className="lg:col-span-2 bg-white p-4 shadow rounded flex flex-col gap-4">
               <div className="flex gap-4 mb-2 text-sm">
                   <label className="flex items-center gap-2">
                       <input type="checkbox" checked={showRaw} onChange={e => setShowRaw(e.target.checked)} />
                       Show Raw Points
                   </label>
                   <label className="flex items-center gap-2">
                       <input type="checkbox" checked={showFitted} onChange={e => setShowFitted(e.target.checked)} />
                       Show Fitted Curves
                   </label>
               </div>
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
                     legend: { orientation: 'h', y: -0.2 }
                 }}
                 useResizeHandler={true}
                 style={{ width: "100%", height: "100%" }}
               />

               {/* Duty Point Evaluation */}
               <div className="mt-4 border-t pt-4">
                   <h3 className="font-bold mb-2">Duty Point Evaluation</h3>
                   <div className="flex flex-wrap gap-4 items-end">
                       <div>
                           <label htmlFor="duty-flow" className="block text-xs font-bold mb-1">Flow ({curveSet.units.flow})</label>
                           <input
                             id="duty-flow"
                             type="number"
                             className="border p-1 rounded w-24"
                             value={dutyFlow}
                             onChange={e => setDutyFlow(e.target.value)}
                           />
                       </div>
                       <div>
                           <label htmlFor="duty-head" className="block text-xs font-bold mb-1">Target Head ({curveSet.units.head})</label>
                           <input
                             id="duty-head"
                             type="number"
                             className="border p-1 rounded w-24"
                             value={dutyHead}
                             onChange={e => setDutyHead(e.target.value)}
                           />
                       </div>
                       <button
                         onClick={handleEvaluate}
                         className="bg-purple-600 text-white px-3 py-1 rounded hover:bg-purple-700 text-sm h-8"
                       >
                           Evaluate
                       </button>
                   </div>

                   {dutyResult && Object.keys(dutyResult).length > 0 && (
                       <div className="mt-2 text-sm bg-gray-50 p-2 rounded">
                           {dutyResult.head !== undefined && (
                               <div className="flex gap-4">
                                   <span><strong>Predicted Head:</strong> {dutyResult.head?.toFixed(2)}</span>
                                   {dutyResult.residuals && (
                                       <span className={dutyResult.residuals.pass ? "text-green-600" : "text-red-600"}>
                                           Residual: {dutyResult.residuals.value.toFixed(2)} ({dutyResult.residuals.pass ? "Pass" : "Fail"})
                                       </span>
                                   )}
                               </div>
                           )}
                           {dutyResult.efficiency !== undefined && <div><strong>Predicted Eff:</strong> {dutyResult.efficiency?.toFixed(2)}%</div>}
                           {dutyResult.power !== undefined && <div><strong>Predicted Power:</strong> {dutyResult.power?.toFixed(2)}</div>}
                           {dutyResult.warnings?.length > 0 && (
                               <div className="text-orange-600 mt-1">
                                   <strong>Warnings:</strong> {dutyResult.warnings.join(', ')}
                               </div>
                           )}
                           {dutyResult.extrapolation && <div className="text-orange-600">Extrapolation detected.</div>}
                       </div>
                   )}
               </div>
           </div>

           {/* Editor Area */}
           <div className="bg-gray-50 p-4 rounded border">
               <h3 className="font-bold mb-4">Edit Curve Data</h3>

               <div className="mb-4">
                   <label htmlFor="series-type" className="block text-sm font-medium mb-1">Series Type</label>
                   <select
                     id="series-type"
                     value={inputType}
                     onChange={(e) => {
                         setInputType(e.target.value as any);
                         setValidationResult(null);
                     }}
                     className="w-full border p-2 rounded"
                   >
                       <option value="head">Head vs Flow</option>
                       <option value="efficiency">Efficiency vs Flow</option>
                       <option value="power">Power vs Flow</option>
                   </select>
               </div>

               <div className="mb-4">
                   <label htmlFor="data-input" className="block text-sm font-medium mb-1">Paste Data (Flow, Value)</label>
                   <p className="text-xs text-gray-500 mb-2">Paste from Excel or CSV. First column flow, second value.</p>
                   <textarea
                       id="data-input"
                       className={`w-full h-40 p-2 border rounded font-mono text-sm ${validationResult?.blocking_errors?.length ? 'border-red-500' : ''}`}
                       value={inputText}
                       onChange={(e) => setInputText(e.target.value)}
                       placeholder={`0 100\n100 95\n200 85...`}
                   />
                   {isValidating && <p className="text-xs text-gray-500 mt-1">Validating...</p>}
               </div>

               {/* Validation Feedback */}
               {validationResult && (
                   <div className="mb-4 text-sm">
                       {validationResult.blocking_errors?.length > 0 && (
                           <div className="bg-red-100 p-2 rounded text-red-700 mb-2">
                               <strong>Errors:</strong>
                               <ul className="list-disc pl-4">
                                   {validationResult.blocking_errors.map((e: any, i: number) => (
                                       <li key={i}>{e.message}</li>
                                   ))}
                               </ul>
                           </div>
                       )}
                       {validationResult.warnings?.length > 0 && (
                           <div className="bg-yellow-100 p-2 rounded text-yellow-700 mb-2">
                               <strong>Warnings:</strong>
                               <ul className="list-disc pl-4">
                                   {validationResult.warnings.map((w: any, i: number) => (
                                       <li key={i}>{w.message}</li>
                                   ))}
                               </ul>
                           </div>
                       )}
                       {!validationResult.blocking_errors?.length && validationResult.normalized_points?.length > 0 && (
                           <div className="text-green-600 text-xs">
                               ✓ {validationResult.normalized_points.length} valid points found.
                           </div>
                       )}
                   </div>
               )}

               <button
                   onClick={handleSave}
                   disabled={validationResult?.blocking_errors?.length > 0 || !inputText.trim()}
                   className={`w-full py-2 rounded text-white ${
                       validationResult?.blocking_errors?.length > 0 || !inputText.trim()
                       ? 'bg-gray-400 cursor-not-allowed'
                       : 'bg-blue-600 hover:bg-blue-700'
                   }`}
               >
                   Save Series
               </button>

               <div className="mt-6 border-t pt-4">
                   <h4 className="font-bold text-sm mb-2">Existing Series</h4>
                   <ul>
                       {curveSet.series.map((s: any) => (
                           <li key={s.id} className="flex flex-col text-sm py-2 border-b last:border-0">
                               <div className="flex justify-between items-center">
                                   <span className="capitalize font-semibold">{s.type}</span>
                                   <span className="text-xs text-gray-500">
                                       {s.points.length} pts
                                   </span>
                               </div>
                               {s.fit_model_type && (
                                   <div className="text-xs text-gray-500 mt-1">
                                       Fit: {s.fit_model_type} (R²: {s.fit_quality?.r2?.toFixed(3) || 'N/A'})
                                   </div>
                               )}
                               {s.validation_warnings?.length > 0 && (
                                   <div className="text-xs text-orange-600 mt-1">
                                       {s.validation_warnings.length} warnings
                                   </div>
                               )}
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
