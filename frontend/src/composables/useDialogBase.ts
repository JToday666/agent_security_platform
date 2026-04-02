// 通用对话框基础逻辑
// 供 LoginDialog、ConfirmDialog 等对话框组件复用

import { ref } from "vue";

export const useDialogBase = () => {
  const isOpen = ref(false);

  const open = (): void => {
    isOpen.value = true;
  };

  const close = (): void => {
    isOpen.value = false;
  };

  const handleOverlayClick = (event: MouseEvent): void => {
    // 仅当点击在 overlay 本身时关闭（不是点击在 modal-card 上）
    if (event.target === event.currentTarget) {
      close();
    }
  };

  const handleKeyDown = (event: KeyboardEvent): void => {
    // Esc 键关闭对话框
    if (event.key === "Escape") {
      close();
    }
  };

  return {
    isOpen,
    open,
    close,
    handleOverlayClick,
    handleKeyDown,
  };
};
