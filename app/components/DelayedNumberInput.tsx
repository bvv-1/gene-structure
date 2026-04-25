"use client";

import { NumberInput, type NumberInputProps } from "@mantine/core";
import { type KeyboardEvent, useEffect, useState } from "react";

type DelayedNumberInputProps = Omit<NumberInputProps, "onChange"> & {
  value: number | "" | undefined;
  onChange: (value: number | "") => void;
};

/**
 * onBlur または Enter キー押下時に親へ値を通知する NumberInput ラッパー
 * 入力中は内部状態のみを更新し、確定時に onChange を呼び出す
 */
export function DelayedNumberInput({
  value,
  onChange,
  ...props
}: DelayedNumberInputProps) {
  const [localValue, setLocalValue] = useState<number | "" | undefined>(value);

  // 親の value が変更された場合、ローカル状態を同期
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleCommit = () => {
    // 値が変更されている場合のみ onChange を呼び出す
    if (localValue !== value) {
      onChange(localValue === undefined ? "" : localValue);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleCommit();
      e.currentTarget.blur();
    }
  };

  return (
    <NumberInput
      {...props}
      value={localValue}
      onChange={(val) => setLocalValue(val === "" ? undefined : Number(val))}
      onBlur={handleCommit}
      onKeyDown={handleKeyDown}
    />
  );
}
