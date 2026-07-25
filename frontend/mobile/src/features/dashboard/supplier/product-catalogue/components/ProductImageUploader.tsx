import React from 'react';
import { View, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { IconButton, Text } from 'react-native-paper';
import type { ProductImage } from '../types';

interface Props {
  images: ProductImage[];
  onAdd: (localUri: string) => void;
  onRemove: (imageId: string) => void;
  maxImages?: number;
}

/**
 * NOTE: image selection requires `expo-image-picker`, which is not yet in
 * the project's dependency reference (Document 10). Install with:
 *     npx expo install expo-image-picker
 * before wiring pickImage() below to a real picker call. Left as a no-op
 * placeholder so this component compiles and renders correctly ahead of
 * that dependency being added.
 */
export function ProductImageUploader({ images, onAdd, onRemove, maxImages = 6 }: Props) {
  const canAddMore = images.length < maxImages;

  async function pickImage() {
    // import * as ImagePicker from 'expo-image-picker';
    // const result = await ImagePicker.launchImageLibraryAsync({
    //   mediaTypes: ImagePicker.MediaTypeOptions.Images,
    //   quality: 0.8,
    // });
    // if (!result.canceled) onAdd(result.assets[0].uri);
    void onAdd; // referenced to avoid unused-var lint until wired up above
  }

  return (
    <View style={styles.row}>
      {[...images]
        .sort((a, b) => a.sortOrder - b.sortOrder)
        .map((image) => (
          <View key={image.id} style={styles.thumbWrapper}>
            <Image source={{ uri: image.imageUrl }} style={styles.thumb} />
            <IconButton
              icon="close-circle"
              size={18}
              style={styles.removeButton}
              onPress={() => onRemove(image.id)}
              accessibilityLabel="Remove image"
            />
          </View>
        ))}
      {canAddMore && (
        <TouchableOpacity style={styles.addTile} onPress={pickImage} accessibilityLabel="Add product image">
          <IconButton icon="plus" size={28} />
          <Text variant="bodySmall">Add photo</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  thumbWrapper: { position: 'relative' },
  thumb: { width: 84, height: 84, borderRadius: 8 },
  removeButton: { position: 'absolute', top: -10, right: -10, margin: 0 },
  addTile: {
    width: 84,
    height: 84,
    borderRadius: 8,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#999',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
