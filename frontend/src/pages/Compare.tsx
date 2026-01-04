import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPumps, getPump } from '../api/client';
import Plot from 'react-plotly.js';
import axios from 'axios';

// Helper to fetch full details of a curve set
const fetchCurveSetDetails = async (curveSetId: number) => {
    // Uses direct axios call, should match client config
    const response = await axios.get(`/api/curve-sets/${curveSetId}`);
    return response.data;
};

const Compare: React.FC = () => {
  const { data: pumps, isLoading: pumpsLoading } = useQuery({ queryKey: ['pumps'], queryFn: getPumps });

  const [selectedPumpIds, setSelectedPumpIds] = useState<number[]>([]);
  const [selectedCurveSetIds, setSelectedCurveSetIds] = useState<number[]>([]);
  const [curveSetsData, setCurveSetsData] = useState<any[]>([]);

  // Fetch full details for selected curve sets
  // In a real app we might use useQueries, but for now a simple effect or manual fetch

  const handleTogglePump = (id: number) => {
      if (selectedPumpIds.includes(id)) {
          setSelectedPumpIds(selectedPumpIds.filter(p => p !== id));
      } else {
          setSelectedPumpIds([...selectedPumpIds, id]);
      }
  };

  const handleToggleCurveSet = async (id: number) => {
      if (selectedCurveSetIds.includes(id)) {
          setSelectedCurveSetIds(selectedCurveSetIds.filter(c => c !== id));
          setCurveSetsData(curveSetsData.filter(c => c.id !== id));
      } else {
          setSelectedCurveSetIds([...selectedCurveSetIds, id]);
          try {
              const data = await fetchCurveSetDetails(id);
              setCurveSetsData([...curveSetsData, data]);
          } catch (e) {
              console.error("Failed to fetch curve set", e);
          }
      }
  };

  // We need to fetch pump details to get their curve sets list if not included in list
  // The list endpoint returns minimal info? No, it returns PumpRead.
  // Wait, `read_pumps` returns `PumpRead` which does NOT include curve sets.
  // I need to fetch details for each selected pump to see its curve sets.

  const [expandedPumps, setExpandedPumps] = useState<{[key: number]: any}>({});

  const expandPump = async (pumpId: number) => {
      if (!expandedPumps[pumpId]) {
          const data = await getPump(pumpId);
          setExpandedPumps(prev => ({...prev, [pumpId]: data}));
      }
  };

  React.useEffect(() => {
      selectedPumpIds.forEach(id => expandPump(id));
  }, [selectedPumpIds]);


  // Prepare Plot Data
  const plotData: any[] = [];
  curveSetsData.forEach((cs, idx) => {
      const headSeries = cs.series.find((s: any) => s.type === 'head');
      if (headSeries) {
          plotData.push({
              x: headSeries.points.map((p: any) => p.flow),
              y: headSeries.points.map((p: any) => p.value),
              type: 'scatter',
              mode: 'lines+markers',
              name: `${cs.name} (Head)`,
              line: { shape: 'spline' }
          });
      }
      // Can also add efficiency comparison if desired, maybe in a separate plot or toggle
  });

  return (
    <div className="container mx-auto p-4 flex flex-col h-screen">
      <h1 className="text-2xl font-bold mb-4">Compare Curve Sets</h1>

      <div className="flex flex-1 gap-4 overflow-hidden">
          {/* Sidebar Selection */}
          <div className="w-1/3 bg-white p-4 overflow-y-auto shadow rounded">
              <h2 className="font-bold mb-2">Select Pumps</h2>
              {pumpsLoading ? <p>Loading...</p> : (
                  <ul className="space-y-2">
                      {pumps?.map((pump: any) => (
                          <li key={pump.id} className="border-b pb-2">
                              <div className="flex items-center">
                                  <input
                                      type="checkbox"
                                      checked={selectedPumpIds.includes(pump.id)}
                                      onChange={() => handleTogglePump(pump.id)}
                                      className="mr-2"
                                  />
                                  <span className="font-medium">{pump.manufacturer} {pump.model}</span>
                              </div>

                              {selectedPumpIds.includes(pump.id) && (
                                  <div className="ml-6 mt-2">
                                      {expandedPumps[pump.id] ? (
                                          <ul className="text-sm space-y-1">
                                              {expandedPumps[pump.id].curve_sets.map((cs: any) => (
                                                  <li key={cs.id} className="flex items-center">
                                                      <input
                                                          type="checkbox"
                                                          checked={selectedCurveSetIds.includes(cs.id)}
                                                          onChange={() => handleToggleCurveSet(cs.id)}
                                                          className="mr-2"
                                                      />
                                                      <span>{cs.name}</span>
                                                  </li>
                                              ))}
                                              {expandedPumps[pump.id].curve_sets.length === 0 && <span className="text-gray-400">No curves</span>}
                                          </ul>
                                      ) : <span>Loading curves...</span>}
                                  </div>
                              )}
                          </li>
                      ))}
                  </ul>
              )}
          </div>

          {/* Plot Area */}
          <div className="flex-1 bg-white p-4 shadow rounded flex flex-col">
              {curveSetsData.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                      Select curve sets to compare
                  </div>
              ) : (
                  <Plot
                    data={plotData}
                    layout={{
                        title: 'Comparison (Head vs Flow)',
                        xaxis: { title: 'Flow' },
                        yaxis: { title: 'Head' },
                        autosize: true,
                    }}
                    useResizeHandler={true}
                    style={{ width: "100%", height: "100%" }}
                  />
              )}
          </div>
      </div>
    </div>
  );
};

export default Compare;
