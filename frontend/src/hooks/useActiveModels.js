import { useState, useEffect } from 'react';
import { modelVersionService } from '../services';

export default function useActiveModels() {
  const [activeModels, setActiveModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchActive = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await modelVersionService.getActiveModels();
      setActiveModels(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActive();
  }, []);

  return {
    activeModels,
    loading,
    error,
    refetch: fetchActive,
  };
}
