import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import Button from "../../components/ui/Button";

import {
  useNotifications,
} from "../../context/NotificationContext";

export default function Notifications() {
  const {
    notifications,
    markAsRead,
    clearNotifications,
  } = useNotifications();

  return (
    <section className="py-16">

      <Container>

        <SectionTitle
          title="Notifications"
          subtitle="Stay updated with marketplace activity."
        />

        <div className="flex justify-end mb-6">

          <Button
            onClick={clearNotifications}
          >
            Clear All
          </Button>

        </div>

        {notifications.length === 0 ? (

          <div className="text-center py-20">

            <h2 className="text-2xl font-bold">

              No Notifications

            </h2>

          </div>

        ) : (

          <div className="space-y-5">

            {notifications.map(
              (notification) => (

                <div
                  key={notification.id}
                  className={`
                    border
                    rounded-xl
                    p-5
                    ${
                      notification.read
                        ? "bg-white"
                        : "bg-blue-50"
                    }
                  `}
                >

                  <h2 className="font-bold text-lg">

                    {notification.title}

                  </h2>

                  <p className="mt-2">

                    {notification.message}

                  </p>

                  <p className="text-gray-500 mt-3">

                    {new Date(
                      notification.createdAt
                    ).toLocaleString()}

                  </p>

                  {!notification.read && (

                    <Button
                      className="mt-4"
                      onClick={() =>
                        markAsRead(
                          notification.id
                        )
                      }
                    >
                      Mark as Read
                    </Button>

                  )}

                </div>

              )
            )}

          </div>

        )}

      </Container>

    </section>
  );
}