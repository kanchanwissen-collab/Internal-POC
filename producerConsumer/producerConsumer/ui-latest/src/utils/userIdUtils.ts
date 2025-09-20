

/**
 * Utility functions for generating and validating 16-digit user IDs
 */

/**
 * Generate a secure 16-digit user ID
 * Format: XXXX-XXXX-XXXX-XXXX (with hyphens for readability)
 * Actual storage: XXXXXXXXXXXXXXXX (16 digits without hyphens)
 */
export function generateUserId(): string {
    // Generate 16 random digits
    let userId = '';
    for (let i = 0; i < 16; i++) {
        userId += Math.floor(Math.random() * 10).toString();
    }
    return userId;
}

/**
 * Format user ID with hyphens for display
 * Input: "1234567890123456"
 * Output: "1234-5678-9012-3456"
 */
export function formatUserId(userId: string): string {
    if (userId.length !== 16) {
        throw new Error('User ID must be exactly 16 digits');
    }

    return `${userId.slice(0, 4)}-${userId.slice(4, 8)}-${userId.slice(8, 12)}-${userId.slice(12, 16)}`;
}

/**
 * Remove hyphens from formatted user ID
 * Input: "1234-5678-9012-3456"
 * Output: "1234567890123456"
 */
export function normalizeUserId(userId: string): string {
    return userId.replace(/-/g, '');
}

/**
 * Validate if a string is a valid 16-digit user ID
 */
export function isValidUserId(userId: string): boolean {
    const normalized = normalizeUserId(userId);
    return /^\d{16}$/.test(normalized);
}

/**
 * Generate a unique user ID with collision check
 * This function should be used with database validation to ensure uniqueness
 */
export async function generateUniqueUserId(
    checkExists: (userId: string) => Promise<boolean>
): Promise<string> {
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts) {
        const userId = generateUserId();

        // Check if this ID already exists in the database
        const exists = await checkExists(userId);

        if (!exists) {
            return userId;
        }

        attempts++;
    }

    throw new Error('Failed to generate unique user ID after maximum attempts');
}

/**
 * Mask user ID for display (show only first 4 and last 4 digits)
 * Input: "1234567890123456"
 * Output: "1234-****-****-3456"
 */
export function maskUserId(userId: string): string {
    if (userId.length !== 16) {
        throw new Error('User ID must be exactly 16 digits');
    }

    return `${userId.slice(0, 4)}-****-****-${userId.slice(12, 16)}`;
}

export default {
    generateUserId,
    formatUserId,
    normalizeUserId,
    isValidUserId,
    generateUniqueUserId,
    maskUserId,
};
