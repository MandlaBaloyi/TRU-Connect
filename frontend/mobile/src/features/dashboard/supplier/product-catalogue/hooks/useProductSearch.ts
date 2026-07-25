import { useEffect, useState } from 'react';
import type { ProductFilters } from '../types';
import { useProducts } from './useProducts';

/**
 * Debounces keyword input before it reaches the query, in line with
 * Document 02 \u00a72.5 (low-bandwidth-aware UX).
 */
export function useProductSearch(
  baseFilters: Omit<ProductFilters, 'keyword'> = {},
  debounceMs = 350,
) {
  const [inputValue, setInputValue] = useState('');
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    const handle = setTimeout(() => setKeyword(inputValue.trim()), debounceMs);
    return () => clearTimeout(handle);
  }, [inputValue, debounceMs]);

  const query = useProducts({ ...baseFilters, keyword: keyword || undefined });

  return { inputValue, setInputValue, ...query };
}
