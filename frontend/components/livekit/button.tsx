import * as React from 'react';
import { type VariantProps, cva } from 'class-variance-authority';
import { Slot } from '@radix-ui/react-slot';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  [
    // typography
    'text-xs font-semibold tracking-wider uppercase whitespace-nowrap',

    // layout
    'inline-flex items-center justify-center gap-2 shrink-0 rounded-full cursor-pointer',

    // interaction
    'outline-none transition-all duration-300 ease-out',
    'active:scale-[0.97]',
    'focus-visible:border-ring focus-visible:ring-ring/40 focus-visible:ring-[3px]',

    // disabled
    'disabled:pointer-events-none disabled:opacity-50',

    // invalid
    'aria-invalid:ring-destructive/20 aria-invalid:border-destructive dark:aria-invalid:ring-destructive/40',

    // icons
    "[&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 [&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-white/[0.08] text-foreground',
          'backdrop-blur-md',
          'hover:bg-white/[0.14]',
        ],

        primary: [
          'bg-primary text-primary-foreground',
          'hover:bg-primary/80',
          'shadow-[0_0_20px_rgba(59,130,246,0.35)]',
        ],

        secondary: [
          'bg-foreground/15 text-secondary-foreground',
          'hover:bg-foreground/25',
          'backdrop-blur-md',
        ],

        destructive: [
          'bg-destructive/10 text-destructive',
          'hover:bg-destructive/20',
          'focus-visible:ring-destructive/20',
          'dark:focus-visible:ring-destructive/40',
        ],

        outline: [
          'border border-white/15 bg-transparent',
          'hover:bg-white/[0.08]',
        ],

        ghost: [
          'bg-transparent',
          'hover:bg-white/[0.08]',
        ],

        link: 'text-primary underline-offset-4 hover:underline',
      },

      size: {
        default: 'h-9 px-4 py-2 has-[>svg]:px-3',
        sm: 'h-8 gap-1.5 px-3 has-[>svg]:px-2.5',
        lg: 'h-10 px-6 has-[>svg]:px-4',
        icon: 'size-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
