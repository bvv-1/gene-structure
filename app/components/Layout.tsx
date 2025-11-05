"use client";

import { ActionIcon, Anchor, AppShell, Container, Group } from "@mantine/core";
import { MantineProvider } from "@mantine/core";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import { Notifications } from "@mantine/notifications";
import { IconBrandGithub } from "@tabler/icons-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  return (
    <MantineProvider>
      <Notifications />
      <AppShell
        header={{ height: 80 }}
        footer={{ height: 60 }}
        padding="md"
        className="gradient-bg"
      >
        <AppShell.Header>
          <Container size="xl" h="100%">
            <Group h="100%" justify="space-between" px="md">
              <Group gap="sm">
                <Image
                  src="/logo.png"
                  alt="logo"
                  width={3757 / 20}
                  height={1290 / 20}
                  onClick={() => router.push("/")}
                />
              </Group>
              <Group gap="xl">
                <Anchor href="/" c="dark" underline="hover">
                  Home
                </Anchor>
                <Anchor href="/docs" c="dark" underline="hover">
                  Docs
                </Anchor>
                <Anchor href="/faq" c="dark" underline="hover">
                  FAQ
                </Anchor>
                <ActionIcon
                  component="a"
                  href="https://github.com/bvv-1/gene-structure"
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="subtle"
                  color="dark"
                  size="lg"
                  aria-label="GitHub"
                >
                  <IconBrandGithub size={24} />
                </ActionIcon>
              </Group>
            </Group>
          </Container>
        </AppShell.Header>

        <AppShell.Main>
          <Container size="xl">{children}</Container>
        </AppShell.Main>

        {/* <AppShell.Footer>
          <Container size="xl" h="100%">
            <Group h="100%" justify="center" px="md">
              <Text size="sm" c="dimmed">
                © 2025 geneSTRUCTURE
              </Text>
            </Group>
          </Container>
        </AppShell.Footer> */}
      </AppShell>
    </MantineProvider>
  );
}
