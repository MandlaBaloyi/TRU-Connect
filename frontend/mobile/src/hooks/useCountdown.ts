import { useEffect, useState, useCallback } from "react";

/**
 * Simple countdown hook used for the OTP resend timer.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (OTP Verification)
 */
export function useCountdown(initialSeconds: number) {
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(id);
  }, [secondsLeft]);

  const reset = useCallback(() => setSecondsLeft(initialSeconds), [initialSeconds]);

  return { secondsLeft, isFinished: secondsLeft <= 0, reset };
}
