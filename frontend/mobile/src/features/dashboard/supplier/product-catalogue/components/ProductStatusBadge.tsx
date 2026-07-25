import React from 'react';
import { Chip } from 'react-native-paper';
import { colors } from '@/theme/colors';
import type { Product } from '../types';
import { getStockStatusMeta } from '../services/stockManager';

interface Props {
  product: Pick<Product, 'isPublished' | 'stockStatus'>;
}

// NOTE: adjust these keys if your theme/colors.ts export uses different
// names (see ASSUMPTIONS in generate_product_catalogue.py).
const ROLE_COLOR: Record<'success' | 'warning' | 'danger', string> = {
  success: colors.success,
  warning: colors.warning,
  danger: colors.danger,
};

/**
 * Document 02 \u00a75, \u00a713: status is always communicated with colour + icon +
 * text, never colour alone.
 */
export function ProductStatusBadge({ product }: Props) {
  if (!product.isPublished) {
    return (
      <Chip compact icon="file-document-edit-outline" style={{ backgroundColor: colors.neutral200 }}>
        Draft
      </Chip>
    );
  }

  const meta = getStockStatusMeta(product.stockStatus);
  return (
    <Chip
      compact
      icon={product.stockStatus === 'in_stock' ? 'check-circle-outline' : 'alert-circle-outline'}
      style={{ backgroundColor: `${ROLE_COLOR[meta.colorRole]}22` }}
      textStyle={{ color: ROLE_COLOR[meta.colorRole] }}
    >
      {meta.label}
    </Chip>
  );
}
