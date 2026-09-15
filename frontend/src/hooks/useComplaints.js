import { useState, useEffect, useCallback } from 'react';
import { complaintService } from '../services';

export default function useComplaints(initialFilters = {}) {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await complaintService.getComplaints(filters);
      setComplaints(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load complaints');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  return {
    complaints,
    loading,
    error,
    filters,
    setFilters,
    refetch: fetchComplaints,
  };
}
