import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Utility types for shadcn-svelte components
type Primitive<T> = T extends object ? T : never;

/**
 * Utility type to add element ref to component props
 */
export type WithElementRef<T, E extends HTMLElement = HTMLElement> = T & {
    ref?: E | null;
};

/**
 * Utility type to exclude 'child' prop from component props
 */
export type WithoutChild<T> = Omit<T, 'child'>;

/**
 * Utility type to exclude 'children' prop from component props
 */
export type WithoutChildren<T> = Omit<T, 'children'>;

/**
 * Utility type to exclude both 'children' and 'child' props from component props
 */
export type WithoutChildrenOrChild<T> = Omit<T, 'children' | 'child'>;
