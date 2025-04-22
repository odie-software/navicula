<template>
  <div ref="containerRef" class="view-splitter-container" @mousemove="handleMouseMove" @mouseup="handleMouseUp" @mouseleave="handleMouseUp">
    <slot></slot>
    <!-- Splitter handles will be dynamically added or managed here -->
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, useSlots, watch, nextTick, type VNode } from 'vue';

const slots = useSlots();
const containerRef = ref<HTMLElement | null>(null);
const paneSizes = ref<number[]>([]); // Stores the flex-grow value for each pane
const isDragging = ref(false);
const dragIndex = ref(-1); // Index of the splitter being dragged
const startX = ref(0);
const initialSizes = ref<number[]>([]);

// Function to initialize or update pane sizes based on slot children
const updatePanes = async () => {
  await nextTick(); // Wait for DOM updates
  if (!containerRef.value) return;

  // Convert HTMLCollection to Array to use filter, and ensure elements are HTMLElements
  const children = Array.from(containerRef.value.children).filter((el): el is HTMLElement =>
    el instanceof HTMLElement && el.style.display !== 'none' && !el.classList.contains('splitter-handle')
  );

  const visiblePaneCount = children.length;

  if (visiblePaneCount === 0) {
    paneSizes.value = [];
    return;
  }

  // Initialize sizes equally if not already set or if count changes drastically
  if (paneSizes.value.length !== visiblePaneCount || paneSizes.value.some(s => s === 0)) {
    const equalSize = 1; // Use flex-grow: 1 for equal distribution initially
    paneSizes.value = Array(visiblePaneCount).fill(equalSize);
  }

  // Apply flex-grow styles to visible children
  children.forEach((child, index) => {
    child.style.flexGrow = String(paneSizes.value[index] ?? 1);
    child.style.flexBasis = '0'; // Important for flex-grow to work correctly
    child.style.overflow = 'hidden'; // Prevent content overflow issues
    // Add data attribute for easier identification if needed
    child.dataset.paneIndex = String(index);
  });

  console.log("Pane sizes:", paneSizes.value);
  console.log("Children:", children);

  // Add splitter handles between visible panes
  addSplitterHandles(children);
};


// Function to add splitter handles between panes
const addSplitterHandles = (panes: HTMLElement[]) => {
  // Remove existing splitters first
  containerRef.value?.querySelectorAll('.splitter-handle').forEach(handle => handle.remove());

  if (panes.length < 2) return; // No splitters needed for 0 or 1 pane

  panes.forEach((pane, index) => {
    if (index < panes.length - 1) {
      const handle = document.createElement('div');
      handle.className = 'splitter-handle';
      handle.style.cursor = 'col-resize';
      handle.style.width = '6px'; // Make it easier to grab
      handle.style.backgroundColor = 'var(--splitter-color, #ccc)'; // Use CSS variable or default
      handle.style.flexShrink = '0'; // Prevent handle from shrinking
      handle.dataset.splitterIndex = String(index); // Store index

      handle.addEventListener('mousedown', (e) => handleMouseDown(e, index));

      // Insert handle after the current pane
      pane.after(handle);
    }
  });
};


const handleMouseDown = (event: MouseEvent, index: number) => {
  event.preventDefault(); // Prevent text selection during drag
  isDragging.value = true;
  dragIndex.value = index;
  startX.value = event.clientX;

  // Store initial sizes (flex-grow) of the two panes being resized
  const children = getVisiblePanes();
  if (children.length > index + 1) {
      initialSizes.value = [
          parseFloat(children[index].style.flexGrow || '1'),
          parseFloat(children[index + 1].style.flexGrow || '1')
      ];
  } else {
      // Fallback or error handling if panes aren't found
      initialSizes.value = [1, 1];
  }

  // Add a class to body to indicate dragging state (optional, for global cursor styles)
  document.body.style.cursor = 'col-resize';
};

const handleMouseMove = (event: MouseEvent) => {
  if (!isDragging.value || dragIndex.value === -1 || !containerRef.value) return;

  const dx = event.clientX - startX.value;
  const children = getVisiblePanes(); // Get currently visible panes
  const containerWidth = containerRef.value.offsetWidth;

  if (children.length <= dragIndex.value + 1 || initialSizes.value.length < 2) {
      console.warn("Splitter drag issue: Not enough children or initial sizes.");
      return; // Safety check
  }

  const pane1 = children[dragIndex.value];
  const pane2 = children[dragIndex.value + 1];

  // Calculate the total flexGrow sum of the two panes being resized
  const totalFlexGrow = initialSizes.value[0] + initialSizes.value[1];

  // Estimate the pixel width represented by the total flexGrow
  // This is an approximation as flex-grow distribution isn't linear with pixels
  // A more accurate approach might involve calculating total flexGrow of all panes
  // and distributing based on that, but this is simpler for adjacent panes.
  const totalPixelWidthOfPair = (pane1.offsetWidth + pane2.offsetWidth); // Current combined width

  // Calculate the change in flexGrow based on pixel movement
  // deltaFlex = (pixelsMoved / totalWidthOfPair) * totalFlexGrowOfPair
  const deltaFlex = (dx / totalPixelWidthOfPair) * totalFlexGrow;

  // Calculate new flexGrow values, ensuring they don't go below a minimum (e.g., 0.1)
  const minFlexGrow = 0.1; // Minimum relative size
  let newFlex1 = Math.max(minFlexGrow, initialSizes.value[0] + deltaFlex);
  let newFlex2 = Math.max(minFlexGrow, initialSizes.value[1] - deltaFlex);

  // Adjust if one hits the minimum to maintain the total flexGrow
   if (newFlex1 === minFlexGrow) {
        newFlex2 = totalFlexGrow - minFlexGrow;
    } else if (newFlex2 === minFlexGrow) {
        newFlex1 = totalFlexGrow - minFlexGrow;
    }


  // Update the paneSizes ref array
  const updatedSizes = [...paneSizes.value];
  updatedSizes[dragIndex.value] = newFlex1;
  updatedSizes[dragIndex.value + 1] = newFlex2;
  paneSizes.value = updatedSizes; // Trigger reactivity

  // Apply the new styles directly for immediate feedback
  pane1.style.flexGrow = String(newFlex1);
  pane2.style.flexGrow = String(newFlex2);
};


const handleMouseUp = () => {
  if (isDragging.value) {
    isDragging.value = false;
    dragIndex.value = -1;
    initialSizes.value = [];
    document.body.style.cursor = ''; // Reset global cursor
    // Optional: Persist final sizes if needed
  }
};

// Helper to get currently visible panes
const getVisiblePanes = (): HTMLElement[] => {
    if (!containerRef.value) return [];
    // Select direct children that are HTMLElements and not the splitter handles
    return Array.from(containerRef.value.children)
        .filter(el => el instanceof HTMLElement && !el.classList.contains('splitter-handle') && el.style.display !== 'none') as HTMLElement[];
};


// Watch for changes in slot content (e.g., v-for updates)
watch(() => slots.default?.(), updatePanes, { deep: true, immediate: true });

// Re-initialize on mount
onMounted(() => {
  updatePanes();
  // Add resize observer if needed for container size changes
});

// Clean up listeners
onUnmounted(() => {
  // Mouse move/up listeners are on the container/body, ensure cleanup if attached to body/window
   document.body.style.cursor = ''; // Reset cursor on unmount just in case
});

</script>

<style scoped>
.view-splitter-container {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
  overflow: hidden; /* Important to contain flex items */
  --splitter-color: #e0e0e0; /* Default splitter color */
}

/* Style for the draggable handles */
.splitter-handle {
  flex-shrink: 0; /* Prevent handle from shrinking */
  background-color: var(--splitter-color);
  cursor: col-resize;
  z-index: 10; /* Ensure handle is clickable */
  transition: background-color 0.2s ease; /* Subtle hover effect */
}

.splitter-handle:hover {
  background-color: #bdbdbd; /* Darker color on hover */
}

/* Ensure direct children (panes) behave correctly */
:slotted(*) {
  flex-basis: 0; /* Essential for flex-grow */
  overflow: hidden; /* Prevent content spillover */
  min-width: 50px; /* Optional: Set a minimum width for panes */
}

/* Dark mode adjustments */
.body--dark .view-splitter-container {
    --splitter-color: #424242; /* Darker splitter for dark mode */
}
.body--dark .splitter-handle:hover {
    background-color: #616161;
}

</style>
